# DataAgent 回归测试集 / 基准答案集

## 用途与执行边界

固定业务问题，用于修改 Prompt、SQL 生成、repair_sql、分析逻辑后重新验收。Case 01–09 已采集真实数据库基准；本轮已通过真实 HTTP POST /ask 逐条完成10条 API 端到端回归（模型/数据库/分析/图表响应链路）。没有使用 baseline SQL 代替 DataAgent，没有模拟接口。本轮仅在回归前更新通用实体标识 Prompt 规则，回归执行期间源码未变化。前端浏览器渲染与交互本轮未验证，不包含在 PASS 范围内。

业务口径：销售额 = products.unit_price * orders.quantity，仅计 orders.status = 'paid'。按当前产品单价计算，并非历史成交价。没有时间限制的问题统计当前数据库全部时间。日期使用左闭右开区间。schema.sql 同时包含建库、建表和 seed；本次没有执行它，也没有通过 seed 推算或填入数据库结果。

比较原则：SQL 无需逐字一致，必须满足口径且结果等价。字段别名可不同，按语义映射；金额按十进制精确比较（不要使用浮点数直接判等），数值字符串与数值可规范化比较。无排序要求的结果按维度键比较；Case 03、06、08 检查顺序/排名。不要把 NULL 自动替换为 0。生成的 SQL 必须是单条只读查询。

图表分层：generate_analysis 的内部 type='none' 是不绘图意图；正常 /ask 无图表验收应为 chart=null，前端以 chart 真值决定是否挂载图表。bar/line 的 x_field/y_field 必须存在于实际 result；y_field 必须可转为数值，title 不固定。若别名不同，配置应同步使用真实别名。

## 历史回归摘要

- 初次真实 API 回归：10/10 PASS（2026-10-03 15:19–15:20）；随后成功路径去重版本的复测为9/10 PASS，Case 02仅按产品名分组。
- 本文下方执行记录和最新汇总已更新为实体标识规则修复后的正式8000服务真实回归，旧结果不代表最新代码。

## 本轮真实 API 端到端回归汇总

- 执行日期：2026-10-03（Asia/Shanghai）；逐条单次请求，Case 01 开始于 2026-10-03T17:37:55+08:00，Case 10 开始于 2026-10-03T17:38:27+08:00。
- 通过：10/10；失败：0/10；10次均保存实际响应，不用基准替代模型生成。
- 正式8000 FastAPI已重启并加载本轮实体标识规则；配置文件模型标识为 `deepseek-v4-flash`（来自当前项目 .env 的非秘密模型字段，未查询服务内部模型状态）。
- 当前工作区未提交；generate_sql.py SHA-256：`0d6adeb29db63e6b1e4d03f750d6e043be5f0efb887bd2817e2b5ddc6a63407f`。执行前后业务源码/前端源码/schema 哈希一致。
- 基准保持原采集记录不变；本轮未执行 baseline SQL、未改库。
- 产品/客户实体标识检查：Case 02/06 按 product_id、product_name 分组，Case 08 按 customer_id、customer_name 分组；无名称单独分组。
- 数据口径错误：本轮未发现。图表配置错误：本轮 /ask 响应未发现。
- 本轮不验证浏览器渲染、窗口缩放、所有潜在输入或 repair_sql 故障分支；PASS 只代表这10条问题的当前接口输出，模型后续运行可能变化。

| Case | HTTP | 状态 | 核对重点 |
| --- | --- | --- | --- |
| 01 | 200 | PASS | 查询2026年8月各地区销售额 |
| 02 | 200 | PASS | 查询各产品销售额 |
| 03 | 200 | PASS | 查询2026年7月至9月每月销售额 |
| 04 | 200 | PASS | 查询2026年8月总销售额 |
| 05 | 200 | PASS | 查询2026年8月华南地区销售额 |
| 06 | 200 | PASS | 查询销售额最高的3个产品 |
| 07 | 200 | PASS | 查询各地区已支付订单数量 |
| 08 | 200 | PASS | 查询消费金额最高的客户 |
| 09 | 200 | PASS | 查询1900年1月各地区销售额 |
| 10 | 200 | PASS | 今天吃什么 |

## 基准采集记录

- 采集时间：2026-10-03T15:01:18+08:00。
- 采集状态：使用本机 MySQL 客户端读取项目配置，实际执行 Case 01–09。单个只读事务的一致性快照内采集；未写库、未调用模型、未输出连接凭据。
- 以下结果是当前数据库快照，不声称数据库与 seed 完全一致；数据变化后需要重新采集并人工审核。

实际表行数：

| customers_count | products_count | orders_count |
| --- | --- | --- |
| 8 | 8 | 36 |

实际订单日期范围：

| min_order_date | max_order_date |
| --- | --- |
| 2026-07-03 | 2026-09-18 |

配套 SQL：[baseline_queries.sql](baseline_queries.sql)；操作说明：[Runbook](../docs/runbook.md)。

## Case 01 - 2026年8月各地区销售额

### 用户问题
查询2026年8月各地区销售额

### 测试目的
多表 JOIN、日期过滤、地区聚合及柱状图。

### 必须满足的业务规则
- 单条只读 SELECT，使用真实表和字段，JOIN 按主外键关联，避免重复计数。
- 仅统计 paid 订单；金额使用 SUM(products.unit_price * orders.quantity)。
- 多表 JOIN、日期过滤、地区聚合及柱状图。

### Baseline SQL
```sql
SELECT c.region, SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid' AND o.order_date >= '2026-08-01' AND o.order_date < '2026-09-01'
GROUP BY c.region
ORDER BY c.region;
```

### 基准结果
| region | sales_amount |
| --- | --- |
| 华东 | 14984.00 |
| 华北 | 16085.00 |
| 华南 | 21275.00 |
| 西南 | 2397.00 |

### 基准答案 / 回答验收
按地区比较销售额；结论中的地区及金额必须能逐项对应基准，不得补充不存在的地区。
不固定自然语言措辞；上方实测结果为事实基准，回答中的名称、金额、数量、排序或趋势必须由该结果支持。

### 图表验收
- 有有效分类/时间数据时，`chart.type="bar"`，基准字段为 `x_field="region"`、`y_field="sales_amount"`。
- SQL 若采用等价别名，图表字段同步匹配；前端数据点、排列和金额/计数与 result 一致。
- 实际 result 为空时，chart 应为 null，不强求图表。

### 执行记录

- 状态：**PASS**。
- 实际提交问题：查询2026年8月各地区销售额。
- 请求：`POST http://127.0.0.1:8000/ask`，HTTP 200。
- 执行时间：2026-10-03T17:37:55+08:00；耗时 6.31 秒。
- 执行方式：真实 HTTP 请求当前 FastAPI；未直连执行基准代替 DataAgent；未重试挑选结果。
- 业务语义与回答核对：paid 过滤、8月左闭右开日期、customers/products 主外键 JOIN、地区 GROUP BY、金额公式均正确；地区行序不同但案例不要求排序；回答逐地区金额与基准一致。
- 结果比较：金额用 Decimal 精确比较；非排序案例按维度比较，Case 03/06/08 按返回顺序比较。辅助 ID 投影与等价别名按上方说明处理。
- 图表核对：type/x_field/y_field 与预期一致，字段在 result 中存在，y_field 可转数值。
- 失败原因：无。
- 前端浏览器展示：本轮未验证，不纳入以上状态。

#### DataAgent 实际 SQL

```sql
SELECT c.region,
       SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid'
AND o.order_date >= '2026-08-01'
AND o.order_date < '2026-09-01'
GROUP BY c.region;
```

#### DataAgent 实际 result

```json
[
  {
    "region": "华南",
    "sales_amount": "21275.00"
  },
  {
    "region": "华东",
    "sales_amount": "14984.00"
  },
  {
    "region": "华北",
    "sales_amount": "16085.00"
  },
  {
    "region": "西南",
    "sales_amount": "2397.00"
  }
]
```

#### DataAgent 实际 answer

```json
"2026年8月各地区销售额：华南 21275.00，华东 14984.00，华北 16085.00，西南 2397.00。"
```

#### DataAgent 实际 chart

```json
{
  "type": "bar",
  "x_field": "region",
  "y_field": "sales_amount",
  "title": "2026年8月各地区销售额"
}
```

#### 对照 baseline result

```json
[
  {
    "region": "华东",
    "sales_amount": "14984.00"
  },
  {
    "region": "华北",
    "sales_amount": "16085.00"
  },
  {
    "region": "华南",
    "sales_amount": "21275.00"
  },
  {
    "region": "西南",
    "sales_amount": "2397.00"
  }
]
```

## Case 02 - 各产品销售额

### 用户问题
查询各产品销售额

### 测试目的
产品维度聚合；问题未指定时间时统计当前库全部时间。

### 必须满足的业务规则
- 单条只读 SELECT，使用真实表和字段，JOIN 按主外键关联，避免重复计数。
- 仅统计 paid 订单；金额使用 SUM(products.unit_price * orders.quantity)。
- 产品维度聚合；问题未指定时间时统计当前库全部时间。

### Baseline SQL
```sql
SELECT p.product_id, p.product_name, SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid'
GROUP BY p.product_id, p.product_name
ORDER BY p.product_id;
```

### 基准结果
| product_id | product_name | sales_amount |
| --- | --- | --- |
| 1 | AI助手基础版 | 10479.00 |
| 2 | AI助手Pro | 26973.00 |
| 3 | 数据分析平台 | 17991.00 |
| 4 | 智能客服系统 | 17988.00 |
| 5 | 云服务套餐 | 14382.00 |
| 6 | 企业知识库 | 16887.00 |
| 7 | USB摄像头 | 5382.00 |

### 基准答案 / 回答验收
产品金额与基准一致；按产品 ID 区分同名产品，不得统计未支付或退款订单。
不固定自然语言措辞；上方实测结果为事实基准，回答中的名称、金额、数量、排序或趋势必须由该结果支持。

### 图表验收
- 有有效分类/时间数据时，`chart.type="bar"`，基准字段为 `x_field="product_name"`、`y_field="sales_amount"`。
- SQL 若采用等价别名，图表字段同步匹配；前端数据点、排列和金额/计数与 result 一致。
- 实际 result 为空时，chart 应为 null，不强求图表。

### 执行记录

- 状态：**PASS**。
- 实际提交问题：查询各产品销售额。
- 请求：`POST http://127.0.0.1:8000/ask`，HTTP 200。
- 执行时间：2026-10-03T17:38:01+08:00；耗时 4.06 秒。
- 执行方式：真实 HTTP 请求当前 FastAPI；未直连执行基准代替 DataAgent；未重试挑选结果。
- 业务语义与回答核对：按 product_id 和 product_name 分组，不合并同名产品；paid 过滤、产品 JOIN 和金额公式正确；未添加时间过滤；7个产品金额与基准逐项一致，行序不影响判定。
- 结果比较：金额用 Decimal 精确比较；非排序案例按维度比较，Case 03/06/08 按返回顺序比较。辅助 ID 投影与等价别名按上方说明处理。
- 图表核对：type/x_field/y_field 与预期一致，字段在 result 中存在，y_field 可转数值。
- 失败原因：无。
- 前端浏览器展示：本轮未验证，不纳入以上状态。

#### DataAgent 实际 SQL

```sql
SELECT p.product_id,
       p.product_name,
       SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid'
GROUP BY p.product_id, p.product_name;
```

#### DataAgent 实际 result

```json
[
  {
    "product_id": 2,
    "product_name": "AI助手Pro",
    "sales_amount": "26973.00"
  },
  {
    "product_id": 1,
    "product_name": "AI助手基础版",
    "sales_amount": "10479.00"
  },
  {
    "product_id": 6,
    "product_name": "企业知识库",
    "sales_amount": "16887.00"
  },
  {
    "product_id": 3,
    "product_name": "数据分析平台",
    "sales_amount": "17991.00"
  },
  {
    "product_id": 5,
    "product_name": "云服务套餐",
    "sales_amount": "14382.00"
  },
  {
    "product_id": 4,
    "product_name": "智能客服系统",
    "sales_amount": "17988.00"
  },
  {
    "product_id": 7,
    "product_name": "USB摄像头",
    "sales_amount": "5382.00"
  }
]
```

#### DataAgent 实际 answer

```json
"各产品销售额如下：AI助手Pro为26973.00，AI助手基础版为10479.00，企业知识库为16887.00，数据分析平台为17991.00，云服务套餐为14382.00，智能客服系统为17988.00，USB摄像头为5382.00。"
```

#### DataAgent 实际 chart

```json
{
  "type": "bar",
  "x_field": "product_name",
  "y_field": "sales_amount",
  "title": "各产品销售额"
}
```

#### 对照 baseline result

```json
[
  {
    "product_id": "1",
    "product_name": "AI助手基础版",
    "sales_amount": "10479.00"
  },
  {
    "product_id": "2",
    "product_name": "AI助手Pro",
    "sales_amount": "26973.00"
  },
  {
    "product_id": "3",
    "product_name": "数据分析平台",
    "sales_amount": "17991.00"
  },
  {
    "product_id": "4",
    "product_name": "智能客服系统",
    "sales_amount": "17988.00"
  },
  {
    "product_id": "5",
    "product_name": "云服务套餐",
    "sales_amount": "14382.00"
  },
  {
    "product_id": "6",
    "product_name": "企业知识库",
    "sales_amount": "16887.00"
  },
  {
    "product_id": "7",
    "product_name": "USB摄像头",
    "sales_amount": "5382.00"
  }
]
```

## Case 03 - 2026年7月至9月每月销售额

### 用户问题
查询2026年7月至9月每月销售额

### 测试目的
月份聚合、包含9月的日期边界及时间升序。

### 必须满足的业务规则
- 单条只读 SELECT，使用真实表和字段，JOIN 按主外键关联，避免重复计数。
- 仅统计 paid 订单；金额使用 SUM(products.unit_price * orders.quantity)。
- 月份聚合、包含9月的日期边界及时间升序。

### Baseline SQL
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid'
  AND o.order_date >= '2026-07-01' AND o.order_date < '2026-10-01'
GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
ORDER BY month;
```

### 基准结果
| month | sales_amount |
| --- | --- |
| 2026-07 | 28764.00 |
| 2026-08 | 54741.00 |
| 2026-09 | 26577.00 |

### 基准答案 / 回答验收
月份必须按时间升序；趋势描述只能根据实际金额，不能凭月份猜测增长。无订单月份不自动补零。
不固定自然语言措辞；上方实测结果为事实基准，回答中的名称、金额、数量、排序或趋势必须由该结果支持。

### 图表验收
- 有有效分类/时间数据时，`chart.type="line"`，基准字段为 `x_field="month"`、`y_field="sales_amount"`。
- SQL 若采用等价别名，图表字段同步匹配；前端数据点、排列和金额/计数与 result 一致。
- 实际 result 为空时，chart 应为 null，不强求图表。

### 执行记录

- 状态：**PASS**。
- 实际提交问题：查询2026年7月至9月每月销售额。
- 请求：`POST http://127.0.0.1:8000/ask`，HTTP 200。
- 执行时间：2026-10-03T17:38:05+08:00；耗时 3.25 秒。
- 执行方式：真实 HTTP 请求当前 FastAPI；未直连执行基准代替 DataAgent；未重试挑选结果。
- 业务语义与回答核对：日期范围覆盖7–9月，按 %Y-%m 聚合并 ORDER BY month 升序；paid、产品 JOIN 和金额公式正确；3个月的金额、顺序和回答均与基准一致。
- 结果比较：金额用 Decimal 精确比较；非排序案例按维度比较，Case 03/06/08 按返回顺序比较。辅助 ID 投影与等价别名按上方说明处理。
- 图表核对：type/x_field/y_field 与预期一致，字段在 result 中存在，y_field 可转数值。
- 失败原因：无。
- 前端浏览器展示：本轮未验证，不纳入以上状态。

#### DataAgent 实际 SQL

```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month,
       SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid'
  AND o.order_date >= '2026-07-01'
  AND o.order_date < '2026-10-01'
GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
ORDER BY month;
```

#### DataAgent 实际 result

```json
[
  {
    "month": "2026-07",
    "sales_amount": "28764.00"
  },
  {
    "month": "2026-08",
    "sales_amount": "54741.00"
  },
  {
    "month": "2026-09",
    "sales_amount": "26577.00"
  }
]
```

#### DataAgent 实际 answer

```json
"2026年7月销售额为28764.00，8月销售额为54741.00，9月销售额为26577.00。"
```

#### DataAgent 实际 chart

```json
{
  "type": "line",
  "x_field": "month",
  "y_field": "sales_amount",
  "title": "2026年7月至9月每月销售额"
}
```

#### 对照 baseline result

```json
[
  {
    "month": "2026-07",
    "sales_amount": "28764.00"
  },
  {
    "month": "2026-08",
    "sales_amount": "54741.00"
  },
  {
    "month": "2026-09",
    "sales_amount": "26577.00"
  }
]
```

## Case 04 - 2026年8月总销售额

### 用户问题
查询2026年8月总销售额

### 测试目的
单个指标聚合及不绘图处理。

### 必须满足的业务规则
- 单条只读 SELECT，使用真实表和字段，JOIN 按主外键关联，避免重复计数。
- 仅统计 paid 订单；金额使用 SUM(products.unit_price * orders.quantity)。
- 单个指标聚合及不绘图处理。

### Baseline SQL
```sql
SELECT SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid' AND o.order_date >= '2026-08-01' AND o.order_date < '2026-09-01';
```

### 基准结果
| sales_amount |
| --- |
| 54741.00 |

### 基准答案 / 回答验收
只回答一个总金额，不生成柱状图或折线图。SUM 为 NULL 时说明未查询到数据，不擅自当成零。
不固定自然语言措辞；上方实测结果为事实基准，回答中的名称、金额、数量、排序或趋势必须由该结果支持。

### 图表验收
- `/ask` 返回 `chart=null`，前端不显示图表。内部分析输出允许 `type="none"`，x_field/y_field 应为 null。

### 执行记录

- 状态：**PASS**。
- 实际提交问题：查询2026年8月总销售额。
- 请求：`POST http://127.0.0.1:8000/ask`，HTTP 200。
- 执行时间：2026-10-03T17:38:08+08:00；耗时 2.85 秒。
- 执行方式：真实 HTTP 请求当前 FastAPI；未直连执行基准代替 DataAgent；未重试挑选结果。
- 业务语义与回答核对：paid、8月日期、产品 JOIN 和金额公式正确；返回单个指标54741.00，回答金额一致，chart=null。
- 结果比较：金额用 Decimal 精确比较；非排序案例按维度比较，Case 03/06/08 按返回顺序比较。辅助 ID 投影与等价别名按上方说明处理。
- 图表核对：实际 chart=null，符合不绘图/空数据/拒答要求。
- 失败原因：无。
- 前端浏览器展示：本轮未验证，不纳入以上状态。

#### DataAgent 实际 SQL

```sql
SELECT SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid'
AND o.order_date >= '2026-08-01'
AND o.order_date < '2026-09-01';
```

#### DataAgent 实际 result

```json
[
  {
    "sales_amount": "54741.00"
  }
]
```

#### DataAgent 实际 answer

```json
"2026年8月总销售额为54741.00。"
```

#### DataAgent 实际 chart

```json
null
```

#### 对照 baseline result

```json
[
  {
    "sales_amount": "54741.00"
  }
]
```

## Case 05 - 2026年8月华南销售额

### 用户问题
查询2026年8月华南地区销售额

### 测试目的
地区、日期和支付状态的组合过滤。

### 必须满足的业务规则
- 单条只读 SELECT，使用真实表和字段，JOIN 按主外键关联，避免重复计数。
- 仅统计 paid 订单；金额使用 SUM(products.unit_price * orders.quantity)。
- 地区、日期和支付状态的组合过滤。

### Baseline SQL
```sql
SELECT SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid' AND c.region = '华南'
  AND o.order_date >= '2026-08-01' AND o.order_date < '2026-09-01';
```

### 基准结果
| sales_amount |
| --- |
| 21275.00 |

### 基准答案 / 回答验收
回答必须限定为2026年8月华南地区；金额不能混入其他地区或月份。
不固定自然语言措辞；上方实测结果为事实基准，回答中的名称、金额、数量、排序或趋势必须由该结果支持。

### 图表验收
- `/ask` 返回 `chart=null`，前端不显示图表。内部分析输出允许 `type="none"`，x_field/y_field 应为 null。

### 执行记录

- 状态：**PASS**。
- 实际提交问题：查询2026年8月华南地区销售额。
- 请求：`POST http://127.0.0.1:8000/ask`，HTTP 200。
- 执行时间：2026-10-03T17:38:11+08:00；耗时 2.66 秒。
- 执行方式：真实 HTTP 请求当前 FastAPI；未直连执行基准代替 DataAgent；未重试挑选结果。
- 业务语义与回答核对：paid、8月日期、华南地区过滤及三表 JOIN 正确；金额21275.00与基准一致，chart=null。
- 结果比较：金额用 Decimal 精确比较；非排序案例按维度比较，Case 03/06/08 按返回顺序比较。辅助 ID 投影与等价别名按上方说明处理。
- 图表核对：实际 chart=null，符合不绘图/空数据/拒答要求。
- 失败原因：无。
- 前端浏览器展示：本轮未验证，不纳入以上状态。

#### DataAgent 实际 SQL

```sql
SELECT SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p ON o.product_id = p.product_id
WHERE c.region = '华南'
AND o.status = 'paid'
AND o.order_date >= '2026-08-01'
AND o.order_date < '2026-09-01';
```

#### DataAgent 实际 result

```json
[
  {
    "sales_amount": "21275.00"
  }
]
```

#### DataAgent 实际 answer

```json
"2026年8月华南地区销售额为21275.00元。"
```

#### DataAgent 实际 chart

```json
null
```

#### 对照 baseline result

```json
[
  {
    "sales_amount": "21275.00"
  }
]
```

## Case 06 - 销售额最高的3个产品

### 用户问题
查询销售额最高的3个产品

### 测试目的
产品聚合、降序排名和 LIMIT 3。

### 必须满足的业务规则
- 单条只读 SELECT，使用真实表和字段，JOIN 按主外键关联，避免重复计数。
- 仅统计 paid 订单；金额使用 SUM(products.unit_price * orders.quantity)。
- 产品聚合、降序排名和 LIMIT 3。

### Baseline SQL
```sql
SELECT p.product_id, p.product_name, SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid'
GROUP BY p.product_id, p.product_name
ORDER BY sales_amount DESC, p.product_id ASC
LIMIT 3;
```

### 基准结果
| product_id | product_name | sales_amount |
| --- | --- | --- |
| 2 | AI助手Pro | 26973.00 |
| 3 | 数据分析平台 | 17991.00 |
| 4 | 智能客服系统 | 17988.00 |

### 基准答案 / 回答验收
返回不超过3个产品，金额降序；并列时基准按 product_id 升序选取。若生成 SQL 未设次排序且边界有并列，记录差异供人工裁定，不直接判错。
不固定自然语言措辞；上方实测结果为事实基准，回答中的名称、金额、数量、排序或趋势必须由该结果支持。

### 图表验收
- 有有效分类/时间数据时，`chart.type="bar"`，基准字段为 `x_field="product_name"`、`y_field="sales_amount"`。
- SQL 若采用等价别名，图表字段同步匹配；前端数据点、排列和金额/计数与 result 一致。
- 实际 result 为空时，chart 应为 null，不强求图表。

### 执行记录

- 状态：**PASS**。
- 实际提交问题：查询销售额最高的3个产品。
- 请求：`POST http://127.0.0.1:8000/ask`，HTTP 200。
- 执行时间：2026-10-03T17:38:14+08:00；耗时 3.92 秒。
- 执行方式：真实 HTTP 请求当前 FastAPI；未直连执行基准代替 DataAgent；未重试挑选结果。
- 业务语义与回答核对：按产品 ID/名称 GROUP BY、paid、产品 JOIN 和金额公式正确；ORDER BY sales_amount DESC、LIMIT 3；实际返回 product_id、product_name 和金额均与基准一致；当前前三金额无并列，缺少次排序不构成失败。
- 结果比较：金额用 Decimal 精确比较；非排序案例按维度比较，Case 03/06/08 按返回顺序比较。辅助 ID 投影与等价别名按上方说明处理。
- 图表核对：type/x_field/y_field 与预期一致，字段在 result 中存在，y_field 可转数值。
- 失败原因：无。
- 前端浏览器展示：本轮未验证，不纳入以上状态。

#### DataAgent 实际 SQL

```sql
SELECT p.product_id, p.product_name, SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid'
GROUP BY p.product_id, p.product_name
ORDER BY sales_amount DESC
LIMIT 3;
```

#### DataAgent 实际 result

```json
[
  {
    "product_id": 2,
    "product_name": "AI助手Pro",
    "sales_amount": "26973.00"
  },
  {
    "product_id": 3,
    "product_name": "数据分析平台",
    "sales_amount": "17991.00"
  },
  {
    "product_id": 4,
    "product_name": "智能客服系统",
    "sales_amount": "17988.00"
  }
]
```

#### DataAgent 实际 answer

```json
"销售额最高的3个产品依次为：AI助手Pro，销售额26973.00；数据分析平台，销售额17991.00；智能客服系统，销售额17988.00。"
```

#### DataAgent 实际 chart

```json
{
  "type": "bar",
  "x_field": "product_name",
  "y_field": "sales_amount",
  "title": "销售额最高的3个产品"
}
```

#### 对照 baseline result

```json
[
  {
    "product_id": "2",
    "product_name": "AI助手Pro",
    "sales_amount": "26973.00"
  },
  {
    "product_id": "3",
    "product_name": "数据分析平台",
    "sales_amount": "17991.00"
  },
  {
    "product_id": "4",
    "product_name": "智能客服系统",
    "sales_amount": "17988.00"
  }
]
```

## Case 07 - 各地区已支付订单数量

### 用户问题
查询各地区已支付订单数量

### 测试目的
COUNT 统计订单条数，避免把 quantity 当订单数。

### 必须满足的业务规则
- 单条只读 SELECT，使用真实表和字段，JOIN 按主外键关联，避免重复计数。
- 仅统计 paid 订单；订单数使用 COUNT(*)，不使用 SUM(quantity)。
- COUNT 统计订单条数，避免把 quantity 当订单数。

### Baseline SQL
```sql
SELECT c.region, COUNT(*) AS paid_order_count
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.status = 'paid'
GROUP BY c.region
ORDER BY c.region;
```

### 基准结果
| region | paid_order_count |
| --- | --- |
| 华东 | 8 |
| 华北 | 7 |
| 华南 | 13 |
| 西南 | 3 |

### 基准答案 / 回答验收
回答为订单条数而非销售额或商品数量；各地区计数与基准一致。
不固定自然语言措辞；上方实测结果为事实基准，回答中的名称、金额、数量、排序或趋势必须由该结果支持。

### 图表验收
- 有有效分类/时间数据时，`chart.type="bar"`，基准字段为 `x_field="region"`、`y_field="paid_order_count"`。
- SQL 若采用等价别名，图表字段同步匹配；前端数据点、排列和金额/计数与 result 一致。
- 实际 result 为空时，chart 应为 null，不强求图表。

### 执行记录

- 状态：**PASS**。
- 实际提交问题：查询各地区已支付订单数量。
- 请求：`POST http://127.0.0.1:8000/ask`，HTTP 200。
- 执行时间：2026-10-03T17:38:18+08:00；耗时 2.9 秒。
- 执行方式：真实 HTTP 请求当前 FastAPI；未直连执行基准代替 DataAgent；未重试挑选结果。
- 业务语义与回答核对：COUNT(o.order_id) 与 COUNT(*) 等价：order_id 是非空主键，JOIN 不重复订单；paid、customers JOIN、地区 GROUP BY 正确；计数13/8/7/3与基准按地区一致，未把商品数量当订单数。
- 结果比较：金额用 Decimal 精确比较；非排序案例按维度比较，Case 03/06/08 按返回顺序比较。辅助 ID 投影与等价别名按上方说明处理。
- 图表核对：type/x_field/y_field 与预期一致，字段在 result 中存在，y_field 可转数值。
- 失败原因：无。
- 前端浏览器展示：本轮未验证，不纳入以上状态。

#### DataAgent 实际 SQL

```sql
SELECT c.region, COUNT(o.order_id) AS paid_order_count
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.status = 'paid'
GROUP BY c.region;
```

#### DataAgent 实际 result

```json
[
  {
    "region": "华南",
    "paid_order_count": 13
  },
  {
    "region": "华东",
    "paid_order_count": 8
  },
  {
    "region": "华北",
    "paid_order_count": 7
  },
  {
    "region": "西南",
    "paid_order_count": 3
  }
]
```

#### DataAgent 实际 answer

```json
"已支付订单数量按地区统计为：华南 13 单，华东 8 单，华北 7 单，西南 3 单。"
```

#### DataAgent 实际 chart

```json
{
  "type": "bar",
  "x_field": "region",
  "y_field": "paid_order_count",
  "title": "各地区已支付订单数量"
}
```

#### 对照 baseline result

```json
[
  {
    "region": "华东",
    "paid_order_count": "8"
  },
  {
    "region": "华北",
    "paid_order_count": "7"
  },
  {
    "region": "华南",
    "paid_order_count": "13"
  },
  {
    "region": "西南",
    "paid_order_count": "3"
  }
]
```

## Case 08 - 消费金额最高的客户

### 用户问题
查询消费金额最高的客户

### 测试目的
三表 JOIN、客户身份聚合及最大值排序。

### 必须满足的业务规则
- 单条只读 SELECT，使用真实表和字段，JOIN 按主外键关联，避免重复计数。
- 仅统计 paid 订单；金额使用 SUM(products.unit_price * orders.quantity)。
- 三表 JOIN、客户身份聚合及最大值排序。

### Baseline SQL
```sql
SELECT c.customer_id, c.customer_name, SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid'
GROUP BY c.customer_id, c.customer_name
ORDER BY sales_amount DESC, c.customer_id ASC
LIMIT 1;
```

### 基准结果
| customer_id | customer_name | sales_amount |
| --- | --- | --- |
| 4 | 东方贸易 | 18781.00 |

### 基准答案 / 回答验收
返回一个最高消费客户及金额；同名客户不可合并。并列时基准选择 customer_id 最小者；生成 SQL 返回其他同额第一名需人工确认，不硬性比较姓名。
不固定自然语言措辞；上方实测结果为事实基准，回答中的名称、金额、数量、排序或趋势必须由该结果支持。

### 图表验收
- `/ask` 返回 `chart=null`，前端不显示图表。内部分析输出允许 `type="none"`，x_field/y_field 应为 null。

### 执行记录

- 状态：**PASS**。
- 实际提交问题：查询消费金额最高的客户。
- 请求：`POST http://127.0.0.1:8000/ask`，HTTP 200。
- 执行时间：2026-10-03T17:38:20+08:00；耗时 2.85 秒。
- 执行方式：真实 HTTP 请求当前 FastAPI；未直连执行基准代替 DataAgent；未重试挑选结果。
- 业务语义与回答核对：三表 JOIN、paid、客户 ID/名称 GROUP BY、ORDER BY total_spent DESC、LIMIT 1 正确；total_spent 等价映射为 sales_amount；客户ID 4、东方贸易、18781.00与基准一致，chart=null。
- 结果比较：金额用 Decimal 精确比较；非排序案例按维度比较，Case 03/06/08 按返回顺序比较。辅助 ID 投影与等价别名按上方说明处理。
- 图表核对：实际 chart=null，符合不绘图/空数据/拒答要求。
- 失败原因：无。
- 前端浏览器展示：本轮未验证，不纳入以上状态。

#### DataAgent 实际 SQL

```sql
SELECT c.customer_id,
       c.customer_name,
       SUM(p.unit_price * o.quantity) AS total_spent
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid'
GROUP BY c.customer_id, c.customer_name
ORDER BY total_spent DESC
LIMIT 1;
```

#### DataAgent 实际 result

```json
[
  {
    "customer_id": 4,
    "customer_name": "东方贸易",
    "total_spent": "18781.00"
  }
]
```

#### DataAgent 实际 answer

```json
"消费金额最高的客户是东方贸易，消费金额为 18781.00。"
```

#### DataAgent 实际 chart

```json
null
```

#### 对照 baseline result

```json
[
  {
    "customer_id": "4",
    "customer_name": "东方贸易",
    "sales_amount": "18781.00"
  }
]
```

## Case 09 - 无数据时间段

### 用户问题
查询1900年1月各地区销售额

### 测试目的
使用分组查询验证真正空数组，不以单行 SUM(NULL) 代替空结果。

### 必须满足的业务规则
- 单条只读 SELECT，使用真实表和字段，JOIN 按主外键关联，避免重复计数。
- 仅统计 paid 订单；金额使用 SUM(products.unit_price * orders.quantity)。
- 使用分组查询验证真正空数组，不以单行 SUM(NULL) 代替空结果。

### Baseline SQL
```sql
SELECT c.region, SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid'
  AND o.order_date >= '1900-01-01' AND o.order_date < '1900-02-01'
GROUP BY c.region
ORDER BY c.region;
```

### 基准结果
`[]`（实际查询返回零行）。

### 基准答案 / 回答验收
只有基准实测为空时才验收 result=[]、chart=null、回答说明没有数据，前端显示“暂无查询结果”。若此时间段已有数据，应选择经只读查询确认无数据的新时间段并重新审核基准。
不固定自然语言措辞；上方实测结果为事实基准，回答中的名称、金额、数量、排序或趋势必须由该结果支持。

### 图表验收
- `/ask` 返回 `chart=null`，前端不显示图表。内部分析输出允许 `type="none"`，x_field/y_field 应为 null。

### 执行记录

- 状态：**PASS**。
- 实际提交问题：查询1900年1月各地区销售额。
- 请求：`POST http://127.0.0.1:8000/ask`，HTTP 200。
- 执行时间：2026-10-03T17:38:23+08:00；耗时 3.43 秒。
- 执行方式：真实 HTTP 请求当前 FastAPI；未直连执行基准代替 DataAgent；未重试挑选结果。
- 业务语义与回答核对：paid、1900年1月日期、三表 JOIN、地区分组和金额公式正确；实际 result=[]、chart=null，回答明确无数据；未用 SUM(NULL) 冒充空数组。
- 结果比较：金额用 Decimal 精确比较；非排序案例按维度比较，Case 03/06/08 按返回顺序比较。辅助 ID 投影与等价别名按上方说明处理。
- 图表核对：实际 chart=null，符合不绘图/空数据/拒答要求。
- 失败原因：无。
- 前端浏览器展示：本轮未验证，不纳入以上状态。

#### DataAgent 实际 SQL

```sql
SELECT c.region, SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid'
AND o.order_date >= '1900-01-01'
AND o.order_date < '1900-02-01'
GROUP BY c.region;
```

#### DataAgent 实际 result

```json
[]
```

#### DataAgent 实际 answer

```json
"查询结果为空，未查询到1900年1月各地区销售额数据。"
```

#### DataAgent 实际 chart

```json
null
```

#### 对照 baseline result

```json
[]
```

## Case 10 - 数据库无关问题

### 用户问题
今天吃什么

### 测试目的
验证 CANNOT_ANSWER 拒答路径，不生成虚假 SQL。

### 必须满足的业务规则
- 不生成虚假 SQL；拒答必须走 CANNOT_ANSWER 路径。
- 不执行数据库业务查询，不给出编造的数据或图表。

### Baseline SQL
不适用：此案例不得执行 SQL。预期生成阶段返回 `CANNOT_ANSWER`。

### 基准结果
不适用数据库数值。以下为代码定义的拒答契约，本轮真实 /ask 已返回与下方契约一致的输出：

```json
{"sql":"","result":[],"answer":"无法根据现有数据库回答该问题","chart":null}
```

### 基准答案 / 回答验收
generate_sql 应返回 CANNOT_ANSWER；/ask 返回 sql=""、result=[]、chart=null，answer="无法根据现有数据库回答该问题"。不执行 SQL、不调用 generate_analysis。拒答由模型决定，仍可能需要数据库 schema 和模型服务可用。

### 图表验收
- `/ask` 返回 `chart=null`，前端不显示图表。内部分析输出允许 `type="none"`，x_field/y_field 应为 null。

### 执行记录

- 状态：**PASS**。
- 实际提交问题：今天吃什么。
- 请求：`POST http://127.0.0.1:8000/ask`，HTTP 200。
- 执行时间：2026-10-03T17:38:27+08:00；耗时 1.03 秒。
- 执行方式：真实 HTTP 请求当前 FastAPI；未直连执行基准代替 DataAgent；未重试挑选结果。
- 业务语义与回答核对：实际 sql=""、result=[]、chart=null；answer="无法根据现有数据库回答该问题"，符合拒答契约。接口没有暴露内部模型原文，因此仅验收可观察的拒答结果，不声称抓取了内部 CANNOT_ANSWER。
- 结果比较：金额用 Decimal 精确比较；非排序案例按维度比较，Case 03/06/08 按返回顺序比较。辅助 ID 投影与等价别名按上方说明处理。
- 图表核对：实际 chart=null，符合不绘图/空数据/拒答要求。
- 失败原因：无。
- 前端浏览器展示：本轮未验证，不纳入以上状态。

#### DataAgent 实际 SQL

`""`（空字符串）。

#### DataAgent 实际 result

```json
[]
```

#### DataAgent 实际 answer

```json
"无法根据现有数据库回答该问题"
```

#### DataAgent 实际 chart

```json
null
```

#### 对照 baseline result

```json
[]
```

Case 10 不适用数据库数值基准；[] 为拒答结果契约。

