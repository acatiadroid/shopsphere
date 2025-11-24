-- ================================================================
-- ShopSphere Complete Database Setup Script - MySQL Version
-- ================================================================
-- This script sets up all tables for the ShopSphere e-commerce platform
-- including user authentication, product catalog, payments, and orders
-- ================================================================

-- Drop existing tables if they exist (CASCADE for foreign keys)
-- Order matters due to foreign key constraints
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS cart_items;
DROP TABLE IF EXISTS wishlist;
DROP TABLE IF EXISTS payment_methods;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS shopusers;

-- ================================================================
-- USER AUTHENTICATION TABLES
-- ================================================================

-- ShopUsers Table
CREATE TABLE shopusers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(500) NOT NULL,        -- Stores hashed password
    salt VARCHAR(100) NULL,                 -- Salt for password hashing
    name VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,         -- Admin flag
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,

    -- Indexes for performance
    INDEX IX_shopusers_email (email),
    INDEX IX_shopusers_is_admin (is_admin)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sessions Table (for authentication tokens)
CREATE TABLE sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_token VARCHAR(500) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key relationship
    CONSTRAINT FK_sessions_user_id FOREIGN KEY (user_id)
        REFERENCES shopusers(id) ON DELETE CASCADE,

    -- Indexes for performance
    INDEX IX_sessions_session_token (session_token),
    INDEX IX_sessions_user_id (user_id),
    INDEX IX_sessions_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- PAYMENT METHODS TABLE
-- ================================================================

-- Payment Methods Table (saved payment methods for users)
CREATE TABLE payment_methods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    payment_type VARCHAR(50) NOT NULL,  -- credit_card, debit_card, paypal, apple_pay, google_pay
    card_last_four VARCHAR(4) NULL,     -- Last 4 digits of card (for display)
    card_brand VARCHAR(50) NULL,        -- Visa, Mastercard, Amex, etc.
    cardholder_name VARCHAR(255) NULL,
    expiry_month INT NULL,
    expiry_year INT NULL,
    is_default BOOLEAN DEFAULT FALSE,   -- Default payment method
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,

    -- Foreign keys
    CONSTRAINT FK_payment_methods_user_id FOREIGN KEY (user_id)
        REFERENCES shopusers(id) ON DELETE CASCADE,

    -- Constraints
    CONSTRAINT CHK_payment_methods_type CHECK (payment_type IN ('credit_card', 'debit_card', 'paypal', 'apple_pay', 'google_pay')),
    CONSTRAINT CHK_payment_methods_expiry_month CHECK (expiry_month IS NULL OR (expiry_month >= 1 AND expiry_month <= 12)),
    CONSTRAINT CHK_payment_methods_expiry_year CHECK (expiry_year IS NULL OR expiry_year >= 2024),

    -- Indexes
    INDEX IX_payment_methods_user_id (user_id),
    INDEX IX_payment_methods_is_default (is_default)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- PRODUCT CATALOG TABLES
-- ================================================================

-- Products Table
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    category VARCHAR(100) NOT NULL,
    image_url VARCHAR(500) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT CHK_products_price CHECK (price >= 0),
    CONSTRAINT CHK_products_stock CHECK (stock_quantity >= 0),

    -- Indexes for performance
    INDEX IX_products_category (category),
    INDEX IX_products_name (name),
    INDEX IX_products_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- SHOPPING CART & WISHLIST TABLES
-- ================================================================

-- Cart Items Table (temporary shopping cart)
CREATE TABLE cart_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    CONSTRAINT FK_cart_items_user_id FOREIGN KEY (user_id)
        REFERENCES shopusers(id) ON DELETE CASCADE,
    CONSTRAINT FK_cart_items_product_id FOREIGN KEY (product_id)
        REFERENCES products(id) ON DELETE CASCADE,

    -- Constraints
    CONSTRAINT CHK_cart_items_quantity CHECK (quantity > 0),

    -- Unique constraint: one entry per user-product combination
    CONSTRAINT UQ_cart_items_user_product UNIQUE (user_id, product_id),

    -- Indexes
    INDEX IX_cart_items_user_id (user_id),
    INDEX IX_cart_items_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Wishlist Table
CREATE TABLE wishlist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    CONSTRAINT FK_wishlist_user_id FOREIGN KEY (user_id)
        REFERENCES shopusers(id) ON DELETE CASCADE,
    CONSTRAINT FK_wishlist_product_id FOREIGN KEY (product_id)
        REFERENCES products(id) ON DELETE CASCADE,

    -- Unique constraint: one entry per user-product combination
    CONSTRAINT UQ_wishlist_user_product UNIQUE (user_id, product_id),

    -- Indexes
    INDEX IX_wishlist_user_id (user_id),
    INDEX IX_wishlist_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- ORDER MANAGEMENT TABLES
-- ================================================================

-- Orders Table
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, paid, processing, shipped, delivered, cancelled
    shipping_address TEXT NULL,
    tracking_number VARCHAR(100) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    paid_at DATETIME NULL,
    shipped_at DATETIME NULL,
    delivered_at DATETIME NULL,

    -- Foreign keys
    CONSTRAINT FK_orders_user_id FOREIGN KEY (user_id)
        REFERENCES shopusers(id) ON DELETE RESTRICT,

    -- Constraints
    CONSTRAINT CHK_orders_total_amount CHECK (total_amount >= 0),
    CONSTRAINT CHK_orders_status CHECK (status IN ('pending', 'paid', 'processing', 'shipped', 'delivered', 'cancelled')),

    -- Indexes
    INDEX IX_orders_user_id (user_id),
    INDEX IX_orders_status (status),
    INDEX IX_orders_created_at (created_at),
    INDEX IX_orders_tracking_number (tracking_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Order Items Table (products in each order)
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price_at_purchase DECIMAL(10, 2) NOT NULL,  -- Price when ordered (in case it changes later)

    -- Foreign keys
    CONSTRAINT FK_order_items_order_id FOREIGN KEY (order_id)
        REFERENCES orders(id) ON DELETE CASCADE,
    CONSTRAINT FK_order_items_product_id FOREIGN KEY (product_id)
        REFERENCES products(id) ON DELETE RESTRICT,

    -- Constraints
    CONSTRAINT CHK_order_items_quantity CHECK (quantity > 0),
    CONSTRAINT CHK_order_items_price CHECK (price_at_purchase >= 0),

    -- Indexes
    INDEX IX_order_items_order_id (order_id),
    INDEX IX_order_items_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- PAYMENT TABLES
-- ================================================================

-- Transactions Table (payment records)
CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    user_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,  -- credit_card, debit_card, paypal, apple_pay, google_pay
    status VARCHAR(50) NOT NULL,          -- completed, failed, pending, refunded
    transaction_id VARCHAR(100) NOT NULL UNIQUE,  -- External transaction reference
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    CONSTRAINT FK_transactions_order_id FOREIGN KEY (order_id)
        REFERENCES orders(id) ON DELETE RESTRICT,
    CONSTRAINT FK_transactions_user_id FOREIGN KEY (user_id)
        REFERENCES shopusers(id) ON DELETE RESTRICT,

    -- Constraints
    CONSTRAINT CHK_transactions_amount CHECK (amount >= 0),
    CONSTRAINT CHK_transactions_payment_method CHECK (payment_method IN ('credit_card', 'debit_card', 'paypal', 'apple_pay', 'google_pay')),
    CONSTRAINT CHK_transactions_status CHECK (status IN ('completed', 'failed', 'pending', 'refunded')),

    -- Indexes
    INDEX IX_transactions_order_id (order_id),
    INDEX IX_transactions_user_id (user_id),
    INDEX IX_transactions_transaction_id (transaction_id),
    INDEX IX_transactions_status (status),
    INDEX IX_transactions_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- SEED DATA (Optional - for testing)
-- ================================================================

-- Create admin user (password should be hashed in production)
-- Default admin email: admin@gmail.com
-- You'll need to create this through the signup endpoint with proper password hashing

-- Sample products (optional - uncomment to add sample data)
/*
INSERT INTO products (name, description, price, stock_quantity, category, image_url)
VALUES
    ('Laptop', 'High-performance laptop for work and gaming', 999.99, 50, 'Electronics', 'https://shopsphere.blob.core.windows.net/cdn/laptop.jpg'),
    ('Wireless Mouse', 'Ergonomic wireless mouse with long battery life', 29.99, 200, 'Electronics', 'https://shopsphere.blob.core.windows.net/cdn/mouse.jpg'),
    ('Office Chair', 'Comfortable ergonomic office chair', 199.99, 30, 'Furniture', 'https://shopsphere.blob.core.windows.net/cdn/chair.jpg'),
    ('Desk Lamp', 'LED desk lamp with adjustable brightness', 39.99, 100, 'Furniture', 'https://shopsphere.blob.core.windows.net/cdn/lamp.jpg'),
    ('Water Bottle', 'Stainless steel insulated water bottle', 24.99, 150, 'Accessories', 'https://shopsphere.blob.core.windows.net/cdn/bottle.jpg');
*/

-- ================================================================
-- VERIFICATION QUERIES
-- ================================================================

-- Verify all tables were created successfully
SELECT 'shopusers' AS TableName, COUNT(*) AS RowCount FROM shopusers
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

-- Show table information
SELECT
    t.TABLE_NAME AS TableName,
    c.COLUMN_NAME AS ColumnName,
    c.DATA_TYPE AS DataType,
    c.CHARACTER_MAXIMUM_LENGTH AS MaxLength,
    c.IS_NULLABLE AS IsNullable
FROM information_schema.TABLES t
INNER JOIN information_schema.COLUMNS c ON t.TABLE_NAME = c.TABLE_NAME
WHERE t.TABLE_SCHEMA = DATABASE()
  AND t.TABLE_NAME IN ('shopusers', 'sessions', 'payment_methods', 'products', 'cart_items', 'wishlist', 'orders', 'order_items', 'transactions')
ORDER BY t.TABLE_NAME, c.ORDINAL_POSITION;

-- ================================================================
-- NOTES
-- ================================================================
-- 1. All passwords in shopusers should be hashed using PBKDF2-HMAC-SHA256
-- 2. Session tokens should be generated using secure random token generation
-- 3. Transaction IDs should be unique and follow format: TXN-XXXXXXXXXXXXXXXX
-- 4. Image URLs should point to Azure Blob Storage CDN
-- 5. Remember to set up proper user permissions and firewall rules for MySQL
-- 6. Consider implementing indexes based on actual query patterns
-- 7. Set up automated cleanup for expired sessions using MySQL Events
-- 8. MySQL specific changes from SQL Server:
--    - IDENTITY(1,1) → AUTO_INCREMENT
--    - NVARCHAR → VARCHAR with utf8mb4 charset
--    - NVARCHAR(MAX) → TEXT
--    - BIT → BOOLEAN
--    - DATETIME2 → DATETIME
--    - GETUTCDATE() → CURRENT_TIMESTAMP
--    - ON DELETE NO ACTION → ON DELETE RESTRICT
--    - Added ENGINE=InnoDB for transaction support
--    - Added utf8mb4_unicode_ci collation for proper Unicode support
-- ================================================================
