-- ================================================================
-- ShopSphere Test Data - MySQL Version
-- ================================================================
-- This script populates the database with realistic test data
-- for development and testing purposes
-- ================================================================
-- IMPORTANT: Run each section separately in order due to foreign key dependencies
-- If you get foreign key errors, make sure the parent tables are populated first
-- ================================================================

-- ================================================================
-- USERS (Run this section FIRST)
-- ================================================================
-- Note: In production, passwords should be hashed using PBKDF2-HMAC-SHA256
-- For testing, these are placeholder hashed values
-- User IDs will be: 1=admin, 2=john, 3=sarah, 4=mike, 5=emma, 6=david, 7=lisa, 8=james
INSERT INTO shopusers (email, password, salt, name, is_admin, created_at)
VALUES
    ('admin@shopsphere.com', 'hashed_password_admin_123', 'salt_admin', 'Admin User', TRUE, '2024-01-01 10:00:00'),
    ('john.doe@gmail.com', 'hashed_password_john_456', 'salt_john', 'John Doe', FALSE, '2024-01-15 14:30:00'),
    ('sarah.smith@gmail.com', 'hashed_password_sarah_789', 'salt_sarah', 'Sarah Smith', FALSE, '2024-02-01 09:15:00'),
    ('mike.johnson@gmail.com', 'hashed_password_mike_101', 'salt_mike', 'Mike Johnson', FALSE, '2024-02-10 16:45:00'),
    ('emma.williams@gmail.com', 'hashed_password_emma_202', 'salt_emma', 'Emma Williams', FALSE, '2024-02-20 11:20:00'),
    ('david.brown@gmail.com', 'hashed_password_david_303', 'salt_david', 'David Brown', FALSE, '2024-03-01 13:00:00'),
    ('lisa.davis@gmail.com', 'hashed_password_lisa_404', 'salt_lisa', 'Lisa Davis', FALSE, '2024-03-05 10:30:00'),
    ('james.wilson@gmail.com', 'hashed_password_james_505', 'salt_james', 'James Wilson', FALSE, '2024-03-10 15:00:00');

-- ================================================================
-- VERIFY USERS INSERTED: Should show 8 users
-- ================================================================
SELECT COUNT(*) AS user_count FROM shopusers;

-- ================================================================
-- SESSIONS (Requires: shopusers)
-- ================================================================
INSERT INTO sessions (user_id, session_token, expires_at, created_at)
VALUES
    (2, 'SESSION_TOKEN_john_abc123xyz456def789ghi012', '2024-12-31 23:59:59', NOW()),
    (3, 'SESSION_TOKEN_sarah_jkl345mno678pqr901stu234', '2024-12-31 23:59:59', NOW()),
    (4, 'SESSION_TOKEN_mike_vwx567yza890bcd123efg456', '2024-12-31 23:59:59', NOW()),
    (5, 'SESSION_TOKEN_emma_hij789klm012nop345qrs678', '2024-12-31 23:59:59', NOW());

-- ================================================================
-- PAYMENT METHODS (Requires: shopusers)
-- ================================================================
INSERT INTO payment_methods (user_id, payment_type, card_last_four, card_brand, cardholder_name, expiry_month, expiry_year, is_default, created_at)
VALUES
    (2, 'credit_card', '4242', 'Visa', 'John Doe', 12, 2026, TRUE, '2024-01-16 10:00:00'),
    (2, 'credit_card', '5555', 'Mastercard', 'John Doe', 6, 2027, FALSE, '2024-02-01 14:00:00'),
    (3, 'credit_card', '3782', 'American Express', 'Sarah Smith', 3, 2025, TRUE, '2024-02-02 09:30:00'),
    (3, 'paypal', NULL, NULL, NULL, NULL, NULL, FALSE, '2024-02-15 11:00:00'),
    (4, 'debit_card', '6011', 'Discover', 'Mike Johnson', 9, 2026, TRUE, '2024-02-11 08:00:00'),
    (5, 'credit_card', '4111', 'Visa', 'Emma Williams', 11, 2025, TRUE, '2024-02-21 13:00:00'),
    (6, 'apple_pay', NULL, NULL, NULL, NULL, NULL, TRUE, '2024-03-02 10:00:00'),
    (7, 'google_pay', NULL, NULL, NULL, NULL, NULL, TRUE, '2024-03-06 12:00:00');

-- ================================================================
-- PRODUCTS (No dependencies - can run anytime)
-- ================================================================
INSERT INTO products (name, description, price, stock_quantity, category, image_url, created_at)
VALUES
    -- Electronics
    ('MacBook Pro 16"', 'Powerful laptop with M3 Pro chip, 18GB RAM, 512GB SSD. Perfect for professionals and creatives.', 2499.99, 25, 'Electronics', NULL, '2024-01-01 10:00:00'),
    ('iPhone 15 Pro', 'Latest iPhone with A17 Pro chip, titanium design, and advanced camera system.', 999.99, 50, 'Electronics', NULL, '2024-01-01 10:15:00'),
    ('Sony WH-1000XM5', 'Industry-leading noise canceling wireless headphones with exceptional sound quality.', 399.99, 75, 'Electronics', NULL, '2024-01-02 11:00:00'),
    ('Samsung 4K Monitor 32"', 'Ultra HD 4K monitor with HDR support, perfect for work and entertainment.', 549.99, 40, 'Electronics', NULL, '2024-01-02 11:30:00'),
    ('Logitech MX Master 3S', 'Advanced wireless mouse with ultra-fast scrolling and ergonomic design.', 99.99, 150, 'Electronics', NULL, '2024-01-03 09:00:00'),
    ('iPad Air', '10.9-inch tablet with M1 chip, perfect for creativity and productivity.', 599.99, 60, 'Electronics', NULL, '2024-01-03 09:30:00'),
    ('Sony PlayStation 5', 'Next-gen gaming console with stunning graphics and lightning-fast loading.', 499.99, 30, 'Electronics', NULL, '2024-01-04 10:00:00'),
    ('Canon EOS R6', 'Full-frame mirrorless camera with 20.1MP sensor and 4K video.', 2499.99, 15, 'Electronics', NULL, '2024-01-05 14:00:00'),
    ('Bose SoundLink Speaker', 'Portable Bluetooth speaker with premium sound and 12-hour battery life.', 149.99, 100, 'Electronics', NULL, '2024-01-06 10:00:00'),
    ('Apple AirPods Pro', 'Wireless earbuds with active noise cancellation and spatial audio.', 249.99, 120, 'Electronics', NULL, '2024-01-07 11:00:00'),

    -- Furniture
    ('Herman Miller Aeron Chair', 'Ergonomic office chair with advanced PostureFit support and breathable mesh.', 1395.00, 20, 'Furniture', NULL, '2024-01-08 10:00:00'),
    ('Standing Desk Pro', 'Electric height-adjustable desk with memory presets and cable management.', 799.99, 35, 'Furniture', NULL, '2024-01-08 10:30:00'),
    ('Modern Bookshelf', '5-tier wooden bookshelf with contemporary design, holds up to 200 books.', 189.99, 45, 'Furniture', NULL, '2024-01-09 09:00:00'),
    ('Sofa - 3 Seater', 'Comfortable fabric sofa with deep cushions and modern styling.', 899.99, 25, 'Furniture', NULL, '2024-01-09 09:30:00'),
    ('Coffee Table Oak', 'Solid oak coffee table with storage drawer and minimalist design.', 349.99, 40, 'Furniture', NULL, '2024-01-10 10:00:00'),
    ('Bed Frame Queen', 'Sturdy queen-size platform bed frame with headboard and wooden slats.', 599.99, 30, 'Furniture', NULL, '2024-01-10 11:00:00'),
    ('Dining Table Set', '6-person dining table set with chairs, modern farmhouse style.', 1299.99, 15, 'Furniture', NULL, '2024-01-11 10:00:00'),

    -- Home & Living
    ('LED Desk Lamp', 'Smart LED lamp with wireless charging, adjustable brightness and color temperature.', 79.99, 200, 'Home & Living', NULL, '2024-01-12 10:00:00'),
    ('Dyson V15 Vacuum', 'Cordless vacuum with laser dust detection and powerful suction.', 699.99, 40, 'Home & Living', NULL, '2024-01-12 11:00:00'),
    ('Air Purifier HEPA', 'Smart air purifier with True HEPA filter, covers up to 500 sq ft.', 299.99, 55, 'Home & Living', NULL, '2024-01-13 09:00:00'),
    ('Robot Vacuum', 'Smart robot vacuum with mapping, auto-empty station, and app control.', 499.99, 35, 'Home & Living', NULL, '2024-01-13 10:00:00'),
    ('Instant Pot Duo', '7-in-1 multi-cooker, 6 quart capacity, pressure cooker and more.', 89.99, 80, 'Home & Living', NULL, '2024-01-14 10:00:00'),
    ('KitchenAid Stand Mixer', 'Professional 5-quart stand mixer with 10 speeds and tilt-head design.', 449.99, 50, 'Home & Living', NULL, '2024-01-14 11:00:00'),
    ('Nespresso Machine', 'Premium coffee and espresso maker with milk frother.', 199.99, 70, 'Home & Living', NULL, '2024-01-15 09:00:00'),

    -- Accessories
    ('Leather Laptop Bag', 'Premium genuine leather messenger bag, fits 15" laptops.', 149.99, 60, 'Accessories', NULL, '2024-01-16 10:00:00'),
    ('Stainless Steel Water Bottle', '32oz insulated bottle, keeps drinks cold for 24hrs, hot for 12hrs.', 34.99, 200, 'Accessories', NULL, '2024-01-16 11:00:00'),
    ('Backpack Pro', 'Travel-friendly backpack with laptop compartment and USB charging port.', 89.99, 100, 'Accessories', NULL, '2024-01-17 09:00:00'),
    ('Wireless Charging Pad', '3-in-1 charging station for iPhone, Apple Watch, and AirPods.', 59.99, 150, 'Accessories', NULL, '2024-01-17 10:00:00'),
    ('Smart Watch Band', 'Premium silicone sport band, compatible with Apple Watch, multiple colors.', 29.99, 250, 'Accessories', NULL, '2024-01-18 09:00:00'),
    ('Phone Case Premium', 'Protective case with MagSafe, military-grade drop protection.', 39.99, 180, 'Accessories', NULL, '2024-01-18 10:00:00'),
    ('Sunglasses Designer', 'Polarized UV400 protection sunglasses with premium frames.', 179.99, 75, 'Accessories', NULL, '2024-01-19 10:00:00'),

    -- Sports & Fitness
    ('Yoga Mat Premium', 'Extra thick 6mm yoga mat with carrying strap, non-slip surface.', 49.99, 120, 'Sports & Fitness', NULL, '2024-01-20 10:00:00'),
    ('Dumbbells Set', 'Adjustable dumbbell set 5-52.5 lbs, space-saving design.', 349.99, 40, 'Sports & Fitness', NULL, '2024-01-20 11:00:00'),
    ('Fitness Tracker', 'Advanced fitness band with heart rate monitor, sleep tracking, GPS.', 129.99, 90, 'Sports & Fitness', NULL, '2024-01-21 09:00:00'),
    ('Resistance Bands Set', '5-piece resistance band set with handles, door anchor, and carrying bag.', 29.99, 150, 'Sports & Fitness', NULL, '2024-01-21 10:00:00'),
    ('Running Shoes', 'Lightweight running shoes with responsive cushioning and breathable mesh.', 129.99, 100, 'Sports & Fitness', NULL, '2024-01-22 10:00:00'),
    ('Foam Roller', 'High-density foam roller for muscle recovery and massage therapy.', 34.99, 130, 'Sports & Fitness', NULL, '2024-01-22 11:00:00');

-- ================================================================
-- CART ITEMS (Requires: shopusers, products)
-- ================================================================
INSERT INTO cart_items (user_id, product_id, quantity, added_at)
VALUES
    (2, 1, 1, '2024-03-15 14:30:00'),   -- John has MacBook Pro in cart
    (2, 5, 2, '2024-03-15 14:32:00'),   -- John has 2 Logitech Mouse in cart
    (3, 10, 1, '2024-03-16 10:00:00'),  -- Sarah has AirPods Pro in cart
    (3, 18, 1, '2024-03-16 10:05:00'),  -- Sarah has LED Desk Lamp in cart
    (4, 7, 1, '2024-03-17 16:00:00'),   -- Mike has PS5 in cart
    (4, 9, 1, '2024-03-17 16:02:00'),   -- Mike has Bose Speaker in cart
    (5, 12, 1, '2024-03-18 11:00:00'),  -- Emma has Standing Desk in cart
    (5, 11, 1, '2024-03-18 11:05:00');  -- Emma has Herman Miller Chair in cart

-- ================================================================
-- WISHLIST (Requires: shopusers, products)
-- ================================================================
INSERT INTO wishlist (user_id, product_id, added_at)
VALUES
    (2, 8, '2024-02-01 10:00:00'),   -- John wishes Canon EOS R6
    (2, 11, '2024-02-05 14:00:00'),  -- John wishes Herman Miller Chair
    (3, 1, '2024-02-10 09:00:00'),   -- Sarah wishes MacBook Pro
    (3, 6, '2024-02-15 11:00:00'),   -- Sarah wishes iPad Air
    (3, 25, '2024-02-20 13:00:00'),  -- Sarah wishes Leather Laptop Bag
    (4, 4, '2024-02-25 10:00:00'),   -- Mike wishes Samsung Monitor
    (4, 12, '2024-03-01 14:00:00'),  -- Mike wishes Standing Desk
    (5, 19, '2024-03-05 09:00:00'),  -- Emma wishes Dyson Vacuum
    (5, 23, '2024-03-08 11:00:00'),  -- Emma wishes KitchenAid Mixer
    (6, 2, '2024-03-10 10:00:00'),   -- David wishes iPhone 15 Pro
    (6, 7, '2024-03-12 14:00:00'),   -- David wishes PS5
    (7, 14, '2024-03-14 09:00:00'),  -- Lisa wishes Sofa
    (7, 17, '2024-03-15 11:00:00');  -- Lisa wishes Dining Table Set

-- ================================================================
-- ORDERS (Requires: shopusers)
-- ================================================================
INSERT INTO orders (user_id, total_amount, status, shipping_address, tracking_number, created_at, paid_at, shipped_at, delivered_at)
VALUES
    -- Delivered orders
    (2, 449.98, 'delivered', '123 Main St, Apt 4B, New York, NY 10001, USA', 'TRK1234567890', '2024-01-20 10:00:00', '2024-01-20 10:05:00', '2024-01-21 08:00:00', '2024-01-24 14:30:00'),
    (3, 999.99, 'delivered', '456 Oak Avenue, Los Angeles, CA 90001, USA', 'TRK2345678901', '2024-01-25 14:30:00', '2024-01-25 14:35:00', '2024-01-26 09:00:00', '2024-01-29 16:45:00'),
    (4, 699.98, 'delivered', '789 Pine Road, Chicago, IL 60601, USA', 'TRK3456789012', '2024-02-01 09:15:00', '2024-02-01 09:20:00', '2024-02-02 10:00:00', '2024-02-05 11:20:00'),

    -- Shipped orders
    (5, 2195.98, 'shipped', '321 Elm Street, Houston, TX 77001, USA', 'TRK4567890123', '2024-02-15 16:00:00', '2024-02-15 16:05:00', '2024-02-16 08:00:00', NULL),
    (6, 649.98, 'shipped', '654 Maple Drive, Phoenix, AZ 85001, USA', 'TRK5678901234', '2024-02-20 11:30:00', '2024-02-20 11:35:00', '2024-02-21 09:00:00', NULL),

    -- Processing orders
    (7, 1299.99, 'processing', '987 Birch Lane, Philadelphia, PA 19019, USA', NULL, '2024-03-01 13:45:00', '2024-03-01 13:50:00', NULL, NULL),
    (2, 599.99, 'processing', '123 Main St, Apt 4B, New York, NY 10001, USA', NULL, '2024-03-05 10:00:00', '2024-03-05 10:05:00', NULL, NULL),

    -- Paid but not shipped
    (3, 2499.99, 'paid', '456 Oak Avenue, Los Angeles, CA 90001, USA', NULL, '2024-03-10 15:30:00', '2024-03-10 15:35:00', NULL, NULL),
    (4, 899.99, 'paid', '789 Pine Road, Chicago, IL 60601, USA', NULL, '2024-03-12 09:00:00', '2024-03-12 09:05:00', NULL, NULL),

    -- Pending orders
    (8, 179.98, 'pending', '147 Cedar Court, San Antonio, TX 78201, USA', NULL, '2024-03-15 14:00:00', NULL, NULL, NULL),

    -- Cancelled order
    (5, 799.99, 'cancelled', '321 Elm Street, Houston, TX 77001, USA', NULL, '2024-02-28 10:00:00', NULL, NULL, NULL);

-- ================================================================
-- ORDER ITEMS (Requires: orders, products)
-- ================================================================
INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase)
VALUES
    -- Order 1 (John - Delivered)
    (1, 3, 1, 399.99),   -- Sony Headphones
    (1, 5, 1, 49.99),    -- Logitech Mouse (price changed from 99.99)

    -- Order 2 (Sarah - Delivered)
    (2, 2, 1, 999.99),   -- iPhone 15 Pro

    -- Order 3 (Mike - Delivered)
    (3, 9, 2, 149.99),   -- 2x Bose Speaker (price changed from 149.99 each)
    (4, 3, 1, 399.99),   -- Sony Headphones

    -- Order 4 (Emma - Shipped)
    (4, 11, 1, 1395.00), -- Herman Miller Chair
    (4, 12, 1, 799.99),  -- Standing Desk
    (4, 18, 1, 0.99),    -- LED Lamp (discounted price)

    -- Order 5 (David - Shipped)
    (5, 4, 1, 549.99),   -- Samsung Monitor
    (5, 5, 1, 99.99),    -- Logitech Mouse

    -- Order 6 (Lisa - Processing)
    (6, 17, 1, 1299.99), -- Dining Table Set

    -- Order 7 (John - Processing)
    (7, 6, 1, 599.99),   -- iPad Air

    -- Order 8 (Sarah - Paid)
    (8, 1, 1, 2499.99),  -- MacBook Pro

    -- Order 9 (Mike - Paid)
    (9, 14, 1, 899.99),  -- Sofa

    -- Order 10 (James - Pending)
    (10, 26, 2, 34.99),  -- 2x Water Bottle
    (10, 32, 2, 49.99),  -- 2x Yoga Mat
    (10, 35, 1, 29.99),  -- Resistance Bands

    -- Order 11 (Emma - Cancelled)
    (11, 12, 1, 799.99); -- Standing Desk

-- ================================================================
-- TRANSACTIONS (Requires: orders, shopusers)
-- ================================================================
INSERT INTO transactions (order_id, user_id, amount, payment_method, status, transaction_id, created_at)
VALUES
    -- Completed transactions
    (1, 2, 449.98, 'credit_card', 'completed', 'TXN-20240120100500001', '2024-01-20 10:05:00'),
    (2, 3, 999.99, 'credit_card', 'completed', 'TXN-20240125143500001', '2024-01-25 14:35:00'),
    (3, 4, 699.98, 'debit_card', 'completed', 'TXN-20240201092000001', '2024-02-01 09:20:00'),
    (4, 5, 2195.98, 'credit_card', 'completed', 'TXN-20240215160500001', '2024-02-15 16:05:00'),
    (5, 6, 649.98, 'apple_pay', 'completed', 'TXN-20240220113500001', '2024-02-20 11:35:00'),
    (6, 7, 1299.99, 'google_pay', 'completed', 'TXN-20240301135000001', '2024-03-01 13:50:00'),
    (7, 2, 599.99, 'credit_card', 'completed', 'TXN-20240305100500001', '2024-03-05 10:05:00'),
    (8, 3, 2499.99, 'paypal', 'completed', 'TXN-20240310153500001', '2024-03-10 15:35:00'),
    (9, 4, 899.99, 'debit_card', 'completed', 'TXN-20240312090500001', '2024-03-12 09:05:00'),

    -- Pending transaction
    (10, 8, 179.98, 'credit_card', 'pending', 'TXN-20240315140000001', '2024-03-15 14:00:00'),

    -- Failed transaction (for cancelled order)
    (11, 5, 799.99, 'credit_card', 'failed', 'TXN-20240228100000001', '2024-02-28 10:00:00');

-- ================================================================
-- VERIFICATION QUERIES
-- ================================================================

-- Count records in each table
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
-- SUMMARY
-- ================================================================
-- Test Data Summary:
-- - 8 Users (1 admin, 7 regular users)
-- - 4 Active sessions
-- - 8 Payment methods
-- - 38 Products across 5 categories (Electronics, Furniture, Home & Living, Accessories, Sports & Fitness)
-- - 8 Cart items
-- - 13 Wishlist items
-- - 11 Orders (3 delivered, 2 shipped, 2 processing, 2 paid, 1 pending, 1 cancelled)
-- - 15 Order items
-- - 11 Transactions (9 completed, 1 pending, 1 failed)
-- ================================================================
