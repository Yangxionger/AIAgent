from csv import Error
import os
import json
from pydoc import cli
from urllib import response

from dotenv import load_dotenv
from numpy import roll
from openai import OpenAI
from pydantic import model_validator,ValidationError
from regex import R
from sympy import content

from db import get_database_schema
from db import execute_sql
from schemas import AnalysisOutput, ChartConfig

from visualization import validate_chart_config

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

FEW_SHOT_EXAMPLES = """
示例1：
用户问题：查询所有华南客户
SQL：
SELECT customer_name, region
FROM customers
WHERE region = '华南';

示例2：
用户问题：查询2026年8月华南地区销售额
SQL：
SELECT SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p ON o.product_id = p.product_id
WHERE c.region = '华南'
AND o.status = 'paid'
AND o.order_date >= '2026-08-01'
AND o.order_date < '2026-09-01';

示例3：
用户问题：查询各地区销售额
SQL：
SELECT c.region,
       SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid'
GROUP BY c.region;
"""

BUSINESS_RULES = """
1. 销售额 = products.unit_price * orders.quantity。
2. 只有 orders.status = 'paid' 的订单计入销售额。
3. 只能使用数据库中真实存在的表和字段。
4. 只能生成只读查询。
5. 按产品维度统计时，products.product_id 是产品唯一标识，product_name 主要用于展示。聚合时优先 GROUP BY product_id, product_name，分组必须包含 product_id，不要只使用可能重复的 product_name 区分产品。
6. 按客户维度统计时，customers.customer_id 是客户唯一标识，customer_name 主要用于展示。聚合时优先 GROUP BY customer_id, customer_name，分组必须包含 customer_id，不要只依赖非唯一名称字段区分客户。
7. 区分实体与分类维度：按地区、类别、月份等维度统计时，按用户要求的分类或时间字段聚合；只有按产品或客户实体维度统计时，才使用相应实体 ID，不能额外按实体 ID 分组而改变地区或月份聚合粒度。
"""

def get_sql_context():
    schema = get_database_schema()

    context = f"""
数据库真实结构：
{schema}

业务规则：
{BUSINESS_RULES}

正确 SQL 示例：
{FEW_SHOT_EXAMPLES}
"""

    return context

def generate_sql(question):
    context = get_sql_context()

    prompt = f"""
你是一个 MySQL 数据分析助手。

{context}

用户问题：
{question}

请生成能够回答用户问题的 SQL。

要求：
1. 严格遵守上面的数据库结构和业务规则。
2. 可以参考上面的 SQL 示例。
3. 只返回 SQL。
4. 不要解释。
5. 不要使用 Markdown 代码块。

如果用户的问题无法通过当前数据库中的表和字段回答，
不要生成虚假的 SELECT 语句，
只返回：

CANNOT_ANSWER
"""

    response = client.chat.completions.create(
        model=os.getenv("DEEPSEEK_MODEL"),
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content.strip()

def generate_answer(question, sql, result):
    prompt = f"""
你是一个数据分析助手。

用户问题：
{question}

系统实际执行的 SQL：
{sql}

数据库真实查询结果：
{result}

请直接根据数据库查询结果回答用户的问题。

要求：
1. 只能使用查询结果中的数据，不要编造、猜测或补充不存在的数据。
2. 不需要重新生成 SQL，也不要解释 SQL。
3. 回答简洁、自然，让普通用户能够直接理解。
4. 如果查询结果为空，或者结果中的关键值为 NULL，明确告诉用户没有查询到相关数据。
5. 不要使用 Markdown 格式。
"""

    response = client.chat.completions.create(
        model=os.getenv("DEEPSEEK_MODEL"),
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    answer = response.choices[0].message.content.strip()

    return answer

def repair_sql(question, old_sql, error_message):
    context = get_sql_context()

    prompt = f"""
你是一个 MySQL SQL 修复助手。

{context}

用户原问题：
{question}

之前生成的错误 SQL：
{old_sql}

MySQL 执行错误：
{error_message}

请根据错误信息修复 SQL。

要求：
1. 修复后的 SQL 必须继续满足用户原问题。
2. 严格遵守上面的业务规则。
3. 只能使用真实存在的表和字段。
4. 只能生成只读查询。
5. 只返回修复后的 SQL。
6. 不要解释。
7. 不要使用 Markdown 代码块。
"""

    response = client.chat.completions.create(
        model=os.getenv("DEEPSEEK_MODEL"),
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content.strip()

def generate_analysis(question, sql, result):
    result_json=json.dumps(
        result,
        ensure_ascii=False,
        default=str
    )
    prompt = f"""
你是企业数据分析助手。

用户问题：
{question}

已经执行的 SQL：
{sql}

SQL 查询结果：
{result_json}

你需要完成两个任务：

1. 根据 SQL 查询结果回答用户的问题。
2. 根据查询结果决定是否适合进行数据可视化。

图表类型只允许：

bar：
适合分类数据之间的数值比较。
例如：各地区销售额、各产品销量。

line：
适合时间趋势。
例如：每月销售额、每日订单量。

none：
如果只有单个数值，或者结果不适合绘图。

要求：

1. 只能使用查询结果中真实存在的字段。
2. 不允许编造字段。
3. x_field 必须来自查询结果。
4. y_field 必须是可转换为数字的指标字段。
5. 如果不适合绘图：
   type 必须为 none，
   x_field 和 y_field 必须为 null。
6. answer 只能根据查询结果回答，不允许编造。
7. 只返回 JSON，不要 Markdown，不要其他解释。

严格返回：

{{
  "answer": "回答内容",
  "chart": {{
    "type": "bar 或 line 或 none",
    "x_field": "字段名或null",
    "y_field": "字段名或null",
    "title": "图表标题或null"
  }}
}}
"""
    response=client.chat.completions.create(
        model=os.getenv("DEEPSEEK_MODEL"),
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )
    content=response.choices[0].message.content.strip()

    try:
        data=json.loads(content)
        analysis=AnalysisOutput.model_validate(data)
        return analysis
    except(json.JSONDecodeError,ValidationError):
        return AnalysisOutput(
            answer="数据查询成功，但分析结果生成失败，请查看下方数据。",
            chart=ChartConfig(
                type="none"
            )
        )


def ask_data_agent(question):
    sql=generate_sql(question)
    if sql.strip() == "CANNOT_ANSWER":
        return "", [], "无法根据现有数据库回答该问题",None
    try:
        result=execute_sql(sql)
    except Exception as error:
        sql=repair_sql(
            question,
            sql,
            str(error)
        )
        result=execute_sql(sql)
    
    analysis = generate_analysis(
        question,
        sql,
        result
    )
    answer = analysis.answer

    chart = validate_chart_config(
        analysis.chart.model_dump(),
        result
    )

    
    return sql, result, answer, chart

