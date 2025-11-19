-- ================================================================
-- ShopSphere Session Cleanup Script
-- ================================================================
-- This script removes expired sessions from the database
-- Run this periodically (e.g., daily via scheduled job)
-- ================================================================

-- Remove expired sessions
DELETE FROM sessions
WHERE expires_at < GETUTCDATE();

-- Show cleanup results
SELECT
    'Sessions cleaned up' AS Status,
    @@ROWCOUNT AS DeletedRows,
    GETUTCDATE() AS CleanupTime;

-- Show remaining active sessions
SELECT
    COUNT(*) AS ActiveSessions,
    MIN(expires_at) AS EarliestExpiry,
    MAX(expires_at) AS LatestExpiry
FROM sessions
WHERE expires_at > GETUTCDATE();

-- ================================================================
-- Optional: Create a stored procedure for automated cleanup
-- ================================================================

IF OBJECT_ID('sp_CleanupExpiredSessions', 'P') IS NOT NULL
    DROP PROCEDURE sp_CleanupExpiredSessions;
GO

CREATE PROCEDURE sp_CleanupExpiredSessions
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @DeletedCount INT;

    -- Delete expired sessions
    DELETE FROM sessions
    WHERE expires_at < GETUTCDATE();

    SET @DeletedCount = @@ROWCOUNT;

    -- Log the cleanup (optional - you can create a cleanup_log table)
    SELECT
        'Cleanup completed' AS Status,
        @DeletedCount AS SessionsDeleted,
        GETUTCDATE() AS CleanupTime;

    RETURN @DeletedCount;
END;
GO

-- ================================================================
-- Usage: Execute the stored procedure
-- ================================================================
-- EXEC sp_CleanupExpiredSessions;

-- ================================================================
-- Notes:
-- ================================================================
-- 1. Schedule this to run daily using Azure SQL Database's SQL Agent
--    or Azure Automation
-- 2. Consider adding a cleanup_log table to track cleanup history
-- 3. Sessions expire after 7 days by default (configured in code)
-- ================================================================
