# 数据库基准采集证据

采集时间：2026-10-03T15:01:18+08:00

## META_TABLES

| Tables_in_data_agent |
| --- |
| customers |
| orders |
| products |

## META_CUSTOMERS

| Field | Type | Null | Key | Default | Extra |
| --- | --- | --- | --- | --- | --- |
| customer_id | int | NO | PRI | NULL | auto_increment |
| customer_name | varchar(100) | NO |  | NULL |  |
| region | varchar(50) | NO |  | NULL |  |

## META_PRODUCTS

| Field | Type | Null | Key | Default | Extra |
| --- | --- | --- | --- | --- | --- |
| product_id | int | NO | PRI | NULL | auto_increment |
| product_name | varchar(100) | NO |  | NULL |  |
| category | varchar(50) | NO |  | NULL |  |
| unit_price | decimal(10,2) | NO |  | NULL |  |

## META_ORDERS

| Field | Type | Null | Key | Default | Extra |
| --- | --- | --- | --- | --- | --- |
| order_id | int | NO | PRI | NULL | auto_increment |
| customer_id | int | NO | MUL | NULL |  |
| product_id | int | NO | MUL | NULL |  |
| quantity | int | NO |  | NULL |  |
| order_date | date | NO |  | NULL |  |
| status | varchar(20) | NO |  | NULL |  |

## META_COUNTS

| customers_count | products_count | orders_count |
| --- | --- | --- |
| 8 | 8 | 36 |

## META_DATES

| min_order_date | max_order_date |
| --- | --- |
| 2026-07-03 | 2026-09-18 |

Case 01–09 的真实执行输出已逐项保存于 regression_cases.md。模型/API/前端回归未执行。
