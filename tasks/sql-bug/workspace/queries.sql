-- E-commerce analytics queries with bugs.
-- Database schema:
--   orders(id, customer_id, created_at, status)       status: 'pending','paid','cancelled'
--   order_items(id, order_id, product_id, quantity, unit_price)
--   customers(id, name, email, created_at)
--   products(id, name, category, price)

-- Query 1: Total revenue from paid orders
-- Bug: uses SUM(unit_price) instead of SUM(quantity * unit_price)
SELECT SUM(oi.unit_price) AS total_revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
WHERE o.status = 'paid';


-- Query 2: Top 5 customers by number of paid orders
-- Bug: GROUP BY is on o.id (order id) instead of o.customer_id
SELECT c.name, COUNT(*) AS order_count
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.status = 'paid'
GROUP BY o.id
ORDER BY order_count DESC
LIMIT 5;


-- Query 3: Monthly revenue for the current year
-- Bug: MONTH(created_at) is not standard SQL; also missing year filter in WHERE
-- Fix: use strftime('%m', created_at) for SQLite, and add WHERE strftime('%Y', o.created_at) = strftime('%Y', 'now')
SELECT MONTH(o.created_at) AS month, SUM(oi.quantity * oi.unit_price) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
WHERE o.status = 'paid'
GROUP BY MONTH(o.created_at)
ORDER BY month;


-- Query 4: Products never ordered
-- Bug: uses INNER JOIN instead of LEFT JOIN, so it returns products that WERE ordered
SELECT p.id, p.name
FROM products p
JOIN order_items oi ON oi.product_id = p.id
WHERE oi.id IS NULL;


-- Query 5: Average order value per customer (only customers with >1 order)
-- Bug: HAVING clause filters on alias 'order_count' which is not allowed in standard SQL before SELECT resolves;
--      also the average is computed wrong: should be SUM(oi.quantity*oi.unit_price)/COUNT(DISTINCT o.id)
SELECT c.name,
       COUNT(o.id) AS order_count,
       AVG(oi.unit_price) AS avg_order_value
FROM customers c
JOIN orders o ON o.customer_id = c.id
JOIN order_items oi ON oi.order_id = o.id
WHERE o.status = 'paid'
GROUP BY c.id, c.name
HAVING order_count > 1
ORDER BY avg_order_value DESC;
