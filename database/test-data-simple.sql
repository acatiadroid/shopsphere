-- ================================================================
-- ShopSphere Basic Test Data - MySQL Version
-- ================================================================
-- Simple test data with minimal records for testing
-- Run each section in order (copy/paste one at a time)
-- ================================================================

-- ================================================================
-- SECTION 1: USERS (Run this FIRST)
-- ================================================================
INSERT INTO shopusers (email, password, salt, name, is_admin, created_at)
VALUES
    ('admin@shopsphere.com', 'hashed_password_admin', 'salt_admin', 'Admin User', TRUE, '2024-01-01 10:00:00'),
    ('john@example.com', 'hashed_password_john', 'salt_john', 'John Doe', FALSE, '2024-01-15 14:30:00'),
    ('sarah@example.com', 'hashed_password_sarah', 'salt_sarah', 'Sarah Smith', FALSE, '2024-02-01 09:15:00');

-- Verify users created (should return 3)
SELECT COUNT(*) AS user_count FROM shopusers;

-- ================================================================
-- SECTION 2: PRODUCTS (Run this SECOND)
-- ================================================================
INSERT INTO products (name, description, price, stock_quantity, category, image_url, created_at)
VALUES
    ('Laptop Pro', 'High-performance laptop', 1299.99, 25, 'Electronics', NULL, '2024-01-01 10:00:00'),
    ('Wireless Mouse', 'Ergonomic wireless mouse', 49.99, 100, 'Electronics', NULL, '2024-01-02 11:00:00'),
    ('Office Chair', 'Comfortable office chair', 299.99, 50, 'Furniture', NULL, '2024-01-03 09:00:00'),
    ('Desk Lamp', 'LED desk lamp', 39.99, 75, 'Home & Living', NULL, '2024-01-04 10:00:00'),
    ('Water Bottle', 'Stainless steel water bottle', 24.99, 150, 'Accessories', NULL, '2024-01-05 11:00:00');

-- Verify products created (should return 5)
SELECT COUNT(*) AS product_count FROM products;

-- ================================================================
-- SECTION 3: SESSIONS (Run this THIRD)
-- ================================================================
INSERT INTO sessions (user_id, session_token, expires_at, created_at)
VALUES
    (2, 'SESSION_TOKEN_john_abc123xyz456', '2024-12-31 23:59:59', NOW()),
    (3, 'SESSION_TOKEN_sarah_def789ghi012', '2024-12-31 23:59:59', NOW());

-- Verify sessions created (should return 2)
SELECT COUNT(*) AS session_count FROM sessions;

-- ================================================================
-- SECTION 4: PAYMENT METHODS (Run this FOURTH)
-- ================================================================
INSERT INTO payment_methods (user_id, payment_type, card_last_four, card_brand, cardholder_name, expiry_month, expiry_year, is_default, created_at)
VALUES
    (2, 'credit_card', '4242', 'Visa', 'John Doe', 12, 2026, TRUE, '2024-01-16 10:00:00'),
    (3, 'credit_card', '5555', 'Mastercard', 'Sarah Smith', 6, 2027, TRUE, '2024-02-02 09:30:00');

-- Verify payment methods created (should return 2)
SELECT COUNT(*) AS payment_method_count FROM payment_methods;

-- ================================================================
-- SECTION 5: CART ITEMS (Run this FIFTH)
-- ================================================================
INSERT INTO cart_items (user_id, product_id, quantity, added_at)
VALUES
    (2, 1, 1, '2024-03-15 14:30:00'),
    (2, 2, 2, '2024-03-15 14:32:00'),
    (3, 3, 1, '2024-03-16 10:00:00');

-- Verify cart items created (should return 3)
SELECT COUNT(*) AS cart_item_count FROM cart_items;

-- ================================================================
-- SECTION 6: WISHLIST (Run this SIXTH)
-- ================================================================
INSERT INTO wishlist (user_id, product_id, added_at)
VALUES
    (2, 3, '2024-02-01 10:00:00'),
    (2, 4, '2024-02-05 14:00:00'),
    (3, 1, '2024-02-10 09:00:00');

-- Verify wishlist items created (should return 3)
SELECT COUNT(*) AS wishlist_count FROM wishlist;

-- ================================================================
-- SECTION 7: ORDERS (Run this SEVENTH)
-- ================================================================
INSERT INTO orders (user_id, total_amount, status, shipping_address, tracking_number, created_at, paid_at, shipped_at, delivered_at)
VALUES
    (2, 99.98, 'delivered', '123 Main St, New York, NY 10001', 'TRK1234567890', '2024-01-20 10:00:00', '2024-01-20 10:05:00', '2024-01-21 08:00:00', '2024-01-24 14:30:00'),
    (3, 1299.99, 'shipped', '456 Oak Ave, Los Angeles, CA 90001', 'TRK2345678901', '2024-02-15 16:00:00', '2024-02-15 16:05:00', '2024-02-16 08:00:00', NULL),
    (2, 299.99, 'processing', '123 Main St, New York, NY 10001', NULL, '2024-03-01 13:45:00', '2024-03-01 13:50:00', NULL, NULL),
    (3, 39.99, 'pending', '456 Oak Ave, Los Angeles, CA 90001', NULL, '2024-03-15 14:00:00', NULL, NULL, NULL);

-- Verify orders created (should return 4)
SELECT COUNT(*) AS order_count FROM orders;

-- ================================================================
-- SECTION 8: ORDER ITEMS (Run this EIGHTH)
-- ================================================================
INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase)
VALUES
    (1, 2, 2, 49.99),
    (2, 1, 1, 1299.99),
    (3, 3, 1, 299.99),
    (4, 4, 1, 39.99);

-- Verify order items created (should return 4)
SELECT COUNT(*) AS order_item_count FROM order_items;

-- ================================================================
-- SECTION 9: TRANSACTIONS (Run this NINTH - LAST)
-- ================================================================
INSERT INTO transactions (order_id, user_id, amount, payment_method, status, transaction_id, created_at)
VALUES
    (1, 2, 99.98, 'credit_card', 'completed', 'TXN-20240120100500001', '2024-01-20 10:05:00'),
    (2, 3, 1299.99, 'credit_card', 'completed', 'TXN-20240215160500001', '2024-02-15 16:05:00'),
    (3, 2, 299.99, 'credit_card', 'completed', 'TXN-20240301135000001', '2024-03-01 13:50:00'),
    (4, 3, 39.99, 'credit_card', 'pending', 'TXN-20240315140000001', '2024-03-15 14:00:00');

-- Verify transactions created (should return 4)
SELECT COUNT(*) AS transaction_count FROM transactions;

-- ================================================================
-- FINAL VERIFICATION - ALL TABLES
-- ================================================================
SELECT 'shopusers' AS TableName, COUNT(*) AS RecordCount FROM shopusers
UNION ALL
SELECT 'sessions', COUNT(*) FROM sessions
UNION ALL
SELECT 'payment_methods', COUNT(*) FROM payment_methods
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'cart_items', COUNT(*) FROM cart_items
UNION ALL
SELECT 'wishlist', COUNT(*) FROM wishlist
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions;

-- ================================================================
-- Expected Results:
-- shopusers: 3
-- sessions: 2
-- payment_methods: 2
-- products: 5
-- cart_items: 3
-- wishlist: 3
-- orders: 4
-- order_items: 4
-- transactions: 4
-- ================================================================
