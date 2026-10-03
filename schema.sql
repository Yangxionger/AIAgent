CREATE DATABASE data_agent;

USE data_agent;

CREATE TABLE customers(
    customer_id int primary key AUTO_INCREMENT,
    customer_name varchar(100) NOT NULL,
    region varchar(50) NOT NULL
);

CREATE TABLE products(
    product_id int primary key AUTO_INCREMENT,
    product_name varchar(100) NOT NULL,
    category varchar(50) NOT NULL,
    unit_price Decimal(10,2) NOT NULL
);

CREATE TABLE orders(
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    order_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,

    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    FOREIGN KEY (product_id)
        REFERENCES products(product_id)
);

USE data_agent;

-- customers

INSERT INTO customers (customer_name, region)
VALUES
('南方科技', '华南'),
('鹏城零售', '华南'),
('岭南教育', '华南'),
('东方贸易', '华东'),
('江南数据', '华东'),
('北方制造', '华北'),
('京华科技', '华北'),
('巴蜀商贸', '西南');

-- products

INSERT INTO products (product_name, category, unit_price)
VALUES
('AI助手基础版', '软件', 499.00),
('AI助手Pro', '软件', 999.00),
('数据分析平台', '软件', 1999.00),
('智能客服系统', '软件', 1499.00),
('云服务套餐', '云服务', 799.00),
('企业知识库', 'SaaS', 1299.00),
('USB摄像头', '硬件', 299.00),
('麦克风套装', '硬件', 399.00);

-- orders

INSERT INTO orders
(customer_id, product_id, quantity, order_date, status)
VALUES

-- 2026年7月
(1, 2, 3, '2026-07-03', 'paid'),
(2, 1, 5, '2026-07-05', 'paid'),
(3, 6, 2, '2026-07-08', 'paid'),
(4, 3, 1, '2026-07-10', 'paid'),
(5, 5, 4, '2026-07-12', 'paid'),
(6, 4, 2, '2026-07-15', 'paid'),
(7, 2, 4, '2026-07-18', 'paid'),
(8, 7, 10, '2026-07-20', 'paid'),
(1, 3, 1, '2026-07-22', 'refunded'),
(4, 6, 3, '2026-07-25', 'paid'),
(6, 8, 5, '2026-07-27', 'pending'),
(2, 5, 2, '2026-07-29', 'paid'),

-- 2026年8月
(1, 2, 4, '2026-08-02', 'paid'),
(2, 3, 2, '2026-08-04', 'paid'),
(3, 1, 6, '2026-08-05', 'paid'),
(1, 6, 3, '2026-08-07', 'paid'),
(4, 3, 2, '2026-08-08', 'paid'),
(5, 4, 4, '2026-08-10', 'paid'),
(6, 2, 5, '2026-08-12', 'paid'),
(7, 6, 2, '2026-08-13', 'paid'),
(8, 5, 3, '2026-08-15', 'paid'),
(2, 7, 8, '2026-08-16', 'paid'),
(3, 8, 6, '2026-08-18', 'pending'),
(4, 1, 10, '2026-08-20', 'paid'),
(5, 3, 1, '2026-08-22', 'refunded'),
(6, 4, 3, '2026-08-23', 'paid'),
(7, 5, 5, '2026-08-25', 'paid'),
(1, 3, 2, '2026-08-28', 'paid'),

-- 2026年9月
(1, 4, 2, '2026-09-01', 'paid'),
(2, 2, 6, '2026-09-03', 'paid'),
(3, 5, 4, '2026-09-05', 'paid'),
(4, 6, 3, '2026-09-07', 'paid'),
(5, 2, 5, '2026-09-10', 'paid'),
(6, 3, 2, '2026-09-12', 'paid'),
(7, 1, 8, '2026-09-15', 'pending'),
(8, 4, 1, '2026-09-18', 'paid');

SELECT COUNT(*) FROM customers;

SELECT COUNT(*) FROM products;

SELECT COUNT(*) FROM orders;