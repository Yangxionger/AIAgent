# DataAgent Runbook：操作与故障排查

本文依据当前项目源码编写，适用于本地 Windows / PowerShell 开发运行。没有修改业务代码，也不宣称已完成生产部署或模型端到端验收。

## 1. 项目结构与请求链路

| 文件 | 当前作用 |
| --- | --- |
| `main.py` | FastAPI 应用、CORS、`POST /ask` |
| `schemas.py` | 请求、响应和分析 JSON 的 Pydantic 模型 |
| `generate_sql.py` | SQL Prompt、CANNOT_ANSWER、一次 SQL 修复、分析与降级 |
| `db.py` | MySQL 连接、SQL AST 校验、查询执行、真实 schema 读取 |
| `visualization.py` | 图表字段及数值合法性检查 |
| `schema.sql` | 建库、建表及 seed 数据，包含 INSERT，不能作为只读诊断脚本 |
| `frontend/src/App.vue` | 请求、结果表格、SQL、错误提示和 ECharts |
| `frontend/src/style.css` | 页面布局和样式 |
| `tests/regression_cases.md` | 10 条业务回归案例及基准结果 |
| `tests/baseline_queries.sql` | Case 01–09 的只读 SQL |
| `tests/baseline_capture.md` | 采集时间、实际 schema 和数据范围证据 |

请求链路：Vue 提交 question → `POST /ask` → 读取真实 schema → 模型生成 SQL → SQL 校验和执行 → 失败时调用一次 repair_sql → 执行 SQL → generate_analysis → 校验图表 → 返回 sql/result/answer/chart → Vue 展示。

当前 ask_data_agent 的正常成功路径仅执行一次 SQL；首次校验或执行失败时只生成一次修复 SQL，再执行修复后的 SQL。修复后仍失败则向上抛出，没有无限修复循环。

业务口径：仅 paid 订单计入销售额，金额为当前 `products.unit_price * orders.quantity`；不是订单历史价格。COUNT(*) 是订单条数，SUM(quantity) 是商品件数。默认未指定时间时使用全库数据。

## 2. 环境与配置

从项目根目录启动后端，以便 dotenv 从项目位置找到 `.env`。不要运行 `Get-Content .env`、打印 os.environ 或把配置值粘贴到日志/截图/测试记录中。

| 环境变量名 | 用途 |
| --- | --- |
| `DB_HOST` | MySQL 地址 |
| `DB_PORT` | MySQL 端口，代码默认 3306 |
| `DB_USER` | MySQL 用户 |
| `DB_PASSWORD` | MySQL 密码，仅保存在本地私有配置中 |
| `DB_NAME` | 目标数据库 |
| `DEEPSEEK_API_KEY` | 模型认证密钥，仅保存在本地私有配置中 |
| `DEEPSEEK_MODEL` | 模型标识，当前代码无默认值 |

已存在的 `.gitignore` 忽略 `.env`、`venv/`、`__pycache__/` 和 `*.pyc`。不要把 `.env` 复制到测试目录，也不要把密码写进命令行参数。

当前项目已提供 requirements.txt，直接依赖版本来自已运行后端的 Python 3.13 环境。本次采集使用的默认 Python 环境缺少 FastAPI、uvicorn、PyMySQL、python-dotenv、sqlglot、openai、regex、sympy；这不代表其他 Python 环境也缺失。优先选择原来能运行后端的解释器。以下命令供人工准备新环境：

```powershell
Set-Location 'D:\Code\huawei-ai-24weeks\projects\data-agent'
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

numpy、regex、sympy 在当前 generate_sql.py 顶层被导入，即使没有参与主要流程也需要可导入；不要为了运行文档擅自删除业务文件中的导入。requirements.txt 锁定直接依赖版本，但未锁定全部传递依赖，不能据此声称环境可完全复现。成功运行后在评审过的环境中另行记录 Python 和依赖版本。

前端 package.json 声明 Vue、ECharts、Vite 和 Vue 插件，已有 package-lock.json。使用与该 Vite 版本兼容的 Node 环境。可先检查 `node --version`、`npm --version`；本次前端环境已有 node_modules，无需额外安装 UI 框架。

## 3. 数据库准备与只读检查

优先连接已有数据库，不重新初始化。`schema.sql` 内含 CREATE DATABASE、CREATE TABLE、INSERT：重复执行会失败或重复插入，不能用于修复连接故障。只有确认是专用空测试库、人工审核目标和权限后才考虑初始化；本文不自动执行初始化或任何删除。

使用本机 MySQL 客户端交互连接，在提示符私下输入密码；用你本地配置填写非秘密的连接信息，不在命令中填写密码：

```powershell
mysql --host=<本地配置的主机> --port=<本地配置的端口> --user=<本地配置的用户> --password --default-character-set=utf8mb4
```

`<...>` 是占位符，应替换后再运行。进入 MySQL 后选择本地配置中的数据库，然后执行：

```sql
SELECT 1 AS connection_ok;
SHOW TABLES;
DESCRIBE customers;
DESCRIBE products;
DESCRIBE orders;
SELECT COUNT(*) AS customers_count FROM customers;
SELECT COUNT(*) AS products_count FROM products;
SELECT COUNT(*) AS orders_count FROM orders;
SELECT MIN(order_date) AS min_order_date, MAX(order_date) AS max_order_date FROM orders;
SELECT status, COUNT(*) AS order_count FROM orders GROUP BY status;
```

实际数据库结构和行数以本次查询为准；不要因为 seed 中存在某条记录就认为当前库一定存在。采集证据见 baseline_capture.md。

## 4. 启动与停止

终端 A，项目根目录，使用正确 Python 环境：

```powershell
Set-Location 'D:\Code\huawei-ai-24weeks\projects\data-agent'
.\venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

如果已有可用解释器且不是上述 venv，用该解释器替换命令前缀，不必重复创建环境。终端 B：

```powershell
Set-Location 'D:\Code\huawei-ai-24weeks\projects\data-agent\frontend'
npm run dev -- --host 127.0.0.1
```

缺少前端依赖的新环境可先执行 `npm ci`；本次不安装依赖。前端通常运行在 5173；如果端口占用，Vite 可能改用其他端口，以终端 Local 输出为准。App.vue 的后端地址固定为 `http://127.0.0.1:8000/ask`，必须让后端监听 8000。当前固定回环地址仅适合本机访问，远程浏览器不会自动指向这台开发机。

停止时在各自终端按 Ctrl+C。重新启动前确认自己服务已退出，不终止未知进程。临时恢复可先重启出故障的服务；不得把重跑 seed 当成恢复方法。

## 5. 分层验证

### 5.1 后端路由验证（不调用模型）

```powershell
Invoke-WebRequest -Uri 'http://127.0.0.1:8000/docs' -UseBasicParsing
$spec = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/openapi.json'
$spec.paths.'/ask'
```

预期 /docs 和 /openapi.json 返回 HTTP 200，OpenAPI 包含 POST /ask。没有 GET /health 或 GET /ask；根路径 GET / 返回 404、GET /ask 返回 405 不等于服务异常。OpenAPI 可用不代表数据库和模型可用。

### 5.2 API 业务冒烟（会调用模型，产生实际请求）

在本地执行，不把认证信息加入请求：

```powershell
$body = @{ question = '查询2026年8月总销售额' } | ConvertTo-Json -Compress
$response = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/ask' -Method Post -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
$response | ConvertTo-Json -Depth 10
```

预期返回 sql、result、answer、chart 四个字段；金额与 Case 04 一致，chart=null。接口请求体只有 question，不需要模型密钥。上面展示的响应包含业务数据，应仅在授权范围内查看，分享前脱敏。`question` 缺失时可预期请求校验 422；后端没有空白问题的额外校验，前端才禁用空白输入。

### 5.3 前端验收

浏览器打开 Vite Local 地址，先运行 Case 01/03/04，再运行 Case 09/10。检查按钮 loading 时禁用、加载提示、AI 结论、表格、SQL、柱状图/折线图、单指标不绘图、空结果及拒答。每次新查询应清空上次结果并销毁旧图。将后端停止后提交一次查询，预期通用提示“查询失败，请稍后重试”，检查后再恢复后端。不要将故障演练误记为业务回归通过。

窄屏表格和图表可在卡片内部横向滚动；图表无 resize 监听，窗口尺寸变化后的适配需要实际检查，不能仅凭 CSS 判定通过。

## 6. 回归与基准维护步骤

1. 固定本次数据快照和环境，记录时间、Python/Node 版本、模型标识、Prompt/源码版本（未提交时写“工作区未提交”），不要记录任何密钥。
2. 在已连接的 MySQL 中读取 `tests/baseline_queries.sql`。需要同一快照时先执行下面的事务语句，再 source 文件，最后 ROLLBACK。
3. 按 Case 01–10 问题逐条通过 UI 或 POST /ask 提交，记录实际四个响应字段及 UI 表现。SQL 别名允许等价映射，不逐字比较 Prompt 或自然语言回答。
4. 按每条验收要求判断 SQL 口径、真实结果、回答事实性和图表；Case 03/06/08 额外检查排序。接口成功但金额错误仍是失败，图表字段缺失/错类型也属于失败。
5. 不能连接数据库时，数值标“待人工确认”；模型不可用时标“未执行/受阻”，不要把 baseline 已采集算作模型回归通过。
6. 有差异先确认数据和单价是否变化，再确认 SQL。数据变化时人工审核并更新基准，保留变更原因和采集时间；不能直接覆盖基准来让错误测试通过。

MySQL 客户端内执行（路径使用正斜杠）：

```sql
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY;
source D:/Code/huawei-ai-24weeks/projects/data-agent/tests/baseline_queries.sql
ROLLBACK;
```

一致性快照针对支持事务快照的表（如 InnoDB），不要同时变更 schema。无数据查询特别区分：GROUP BY 无匹配通常返回 []，不带 GROUP BY 的 SUM 无匹配通常返回一行 NULL。Case 09 用前者；不能假设 NULL 代表 0。

建议记录模板：

| Case | 时间/执行人 | SQL口径 | 结果 | 回答 | 图表/UI | 通过/失败/待确认 | 原因 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 01–10，逐条填写 | 待填写 | 未执行 | 未执行 | 未执行 | 未执行 | 未执行 | 待填写 |

repair_sql 的真实触发具有模型随机性，不能因十条问题都正常通过就宣称修复分支通过。需要验证修复时，另行在隔离测试环境用测试替身构造首次执行错误，确认仅修复一次、业务口径仍正确、修复后失败向上抛出；不要修改生产数据或正式业务代码来制造故障。本次没有新增该自动化测试，也没有声称覆盖它。

## 7. 故障排查

| 现象 | 先检查 | 操作与判断 |
| --- | --- | --- |
| ModuleNotFoundError / uvicorn 不能启动 | 当前解释器、当前目录、依赖 | 使用原可用环境；`python -m pip show` 检查缺失包；generate_sql.py 的顶层 numpy/regex/sympy 导入也会阻止启动 |
| 模型客户端初始化失败 | `.env` 是否被读取、API key 是否配置 | 仅在私有环境核对存在性；不打印值；修改配置后重启后端 |
| MySQL 2003 / 2005 / 连接超时 | MySQL 服务、网络、主机/端口 | 用私有客户端连接和 SELECT 1 分层验证；不因连接失败重跑 schema.sql |
| MySQL 1045 | 用户、密码、连接来源授权 | 私下核对凭据和授权，分享日志时移除账号、主机及配置值 |
| MySQL 1049 / 1146 / 1054 | 数据库、表、列是否匹配 | 对照实际 SHOW TABLES / DESCRIBE；不要直接删除数据库；1054 也可能是模型 SQL 错字段 |
| 模型 401 / 429 / 网络错误 | 认证、配额、网络及模型标识 | 核对私有配置和服务状态；记录脱敏状态码；当前应用没有统一重试和用户友好错误映射 |
| POST /ask 返回 422 | JSON 请求体 | 使用 `{ "question": "业务问题" }` 和正确 Content-Type；不要传前端内部 chartConfig 字段 |
| POST /ask 返回 500 | 后端终端中的脱敏异常类型 | 从数据库连接、生成 SQL、SQL 执行、修复、分析调用逐层定位；API 路由没有统一 try/except 包装 |
| 前端只提示查询失败 | 浏览器 Network 的 /ask 和后端日志 | fetch 网络失败或非2xx都会显示通用错误；不要据此直接归因数据库 |
| SQL 被拒绝 | 是否单条 Select/Union | db.validate_sql 会拒绝多语句和其他顶层语句；不要绕过校验来让测试通过 |
| 数值不匹配 | paid、日期边界、JOIN、单价、数量、维度 | 用 baseline SQL 比较；留意退款/待支付订单、漏乘 quantity、同名产品/客户错误合并 |
| 查询成功但分析结果生成失败 | 返回的 answer 是否是固定降级文案 | JSON 解析/Pydantic 校验失败会保留 SQL/result，返回“数据查询成功，但分析结果生成失败，请查看下方数据。”并通常 chart=null；模型网络错误不走这条 JSON 降级分支 |
| 图表不出现 | result、chart、字段、数值 | 空结果、缺字段、字段不在首行或 y 不能转数字都会被校验为 null；单指标不绘图本来就是验收目标 |
| 图表出现但轴名称缺失 | 网络响应配置键名 | 当前前端取数据用 x_field/y_field，但轴/series 名称用 xField/yField；这是现有差异，本次只记录不修复 |
| 图表类型或单指标绘图错误 | 实际 chart.type 及字段 | Pydantic 限定 bar/line/none；validate_chart_config 没有直接排除 type=none，也没有按行数强制不绘图；回归必须独立检查意图，不能认为校验已保证所有规则 |
| 暂无查询结果 | result 是否真的 [] | 无匹配分组与单行 SUM(NULL) 不同；拒答也会因 result=[] 显示这条次要提示 |
| 端口占用 / 请求错误后端 | Vite Local 输出、8000 监听情况 | 不盲目结束未知进程；前端 API 地址固定8000，改后端端口而不改前端会失败 |

日志收集仅记录：时间、Case 编号、HTTP/MySQL 脱敏错误码、异常类型、必要的脱敏 SQL 和数据差异。不要分享原始 `.env`、请求认证头、模型客户端调试日志或未脱敏异常全文。

## 8. 现有边界与本次验证状态

- SQL 校验只验证语句数量及顶层 Select/Union，不是完整的安全策略；没有表白名单、行数限制或应用层查询超时保证。连接账户权限决定数据库能做什么。不要把本项目描述为生产级 SQL 沙箱。
- 当前 CORS 允许所有来源；没有应用鉴权。本文仅描述本地开发操作，不宣称可直接暴露公网。
- 后端无专用健康检查、结构化审计日志或统一异常响应；前端无请求超时逻辑。排查时需要分层确认，不是无限点击重试。
- 本次实际连接 MySQL、读取 schema 和数据范围并执行 Case 01–09，证据与数值见 tests 文档；未执行 seed、未写库。
- 本次没有调用 DeepSeek，没有执行模型/API/前端完整回归。默认 Python 缺少后端依赖，因此没有启动后端来声称端到端通过。
- 所有现有业务源码保持不变；未 git commit / push。后续 Prompt 或业务改动，应复用此案例集，单独记录实际通过率与失败原因。
