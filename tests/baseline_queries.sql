-- 只读基准查询；Case 10 不执行 SQL。

-- Case 01: 2026年8月各地区销售额
SELECT c.region, SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid' AND o.order_date >= '2026-08-01' AND o.order_date < '2026-09-01'
GROUP BY c.region
ORDER BY c.region;

-- Case 02: 各产品销售额
SELECT p.product_id, p.product_name, SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid'
GROUP BY p.product_id, p.product_name
ORDER BY p.product_id;

-- Case 03: 2026年7月至9月每月销售额
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid'
  AND o.order_date >= '2026-07-01' AND o.order_date < '2026-10-01'
GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
ORDER BY month;

-- Case 04: 2026年8月总销售额
SELECT SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid' AND o.order_date >= '2026-08-01' AND o.order_date < '2026-09-01';

-- Case 05: 2026年8月华南销售额
SELECT SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid' AND c.region = '华南'
  AND o.order_date >= '2026-08-01' AND o.order_date < '2026-09-01';

-- Case 06: 销售额最高的3个产品
SELECT p.product_id, p.product_name, SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid'
GROUP BY p.product_id, p.product_name
ORDER BY sales_amount DESC, p.product_id ASC
LIMIT 3;

-- Case 07: 各地区已支付订单数量
SELECT c.region, COUNT(*) AS paid_order_count
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.status = 'paid'
GROUP BY c.region
ORDER BY c.region;

-- Case 08: 消费金额最高的客户
SELECT c.customer_id, c.customer_name, SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid'
GROUP BY c.customer_id, c.customer_name
ORDER BY sales_amount DESC, c.customer_id ASC
LIMIT 1;

-- Case 09: 无数据时间段
SELECT c.region, SUM(p.unit_price * o.quantity) AS sales_amount
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'paid'
  AND o.order_date >= '1900-01-01' AND o.order_date < '1900-02-01'
GROUP BY c.region
ORDER BY c.region;
