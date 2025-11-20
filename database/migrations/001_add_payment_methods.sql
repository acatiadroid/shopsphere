-- ================================================================
-- Migration: Add Payment Methods Table
-- Version: 001
-- Description: Adds payment_methods table to support saved payment methods
-- ================================================================

-- Check if table already exists
IF OBJECT_ID('payment_methods', 'U') IS NULL
BEGIN
    PRINT 'Creating payment_methods table...';

    CREATE TABLE payment_methods (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NOT NULL,
        payment_type NVARCHAR(50) NOT NULL,  -- credit_card, debit_card, paypal, apple_pay, google_pay
        card_last_four NVARCHAR(4) NULL,     -- Last 4 digits of card (for display)
        card_brand NVARCHAR(50) NULL,        -- Visa, Mastercard, Amex, etc.
        cardholder_name NVARCHAR(255) NULL,
        expiry_month INT NULL,
        expiry_year INT NULL,
        is_default BIT DEFAULT 0,            -- Default payment method
        created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        updated_at DATETIME2 NULL,

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
    );

    PRINT 'payment_methods table created successfully.';
END
ELSE
BEGIN
    PRINT 'payment_methods table already exists. Skipping creation.';
END
GO

-- Verify the table was created
IF OBJECT_ID('payment_methods', 'U') IS NOT NULL
BEGIN
    PRINT 'Migration completed successfully.';
    SELECT
        t.name AS TableName,
        c.name AS ColumnName,
        ty.name AS DataType,
        c.max_length AS MaxLength,
        c.is_nullable AS IsNullable
    FROM sys.tables t
    INNER JOIN sys.columns c ON t.object_id = c.object_id
    INNER JOIN sys.types ty ON c.user_type_id = ty.user_type_id
    WHERE t.name = 'payment_methods'
    ORDER BY c.column_id;
END
ELSE
BEGIN
    PRINT 'ERROR: Migration failed. payment_methods table was not created.';
END
GO
