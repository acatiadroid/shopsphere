import hashlib
import logging
import os
import secrets

import pyodbc


def get_db_connection():
    """Create database connection using pyodbc"""
    conn_str = os.environ.get("SqlConnectionString")

    if not conn_str:
        raise ValueError("SqlConnectionString environment variable not set")

    logging.info("Attempting database connection")

    try:
        conn = pyodbc.connect(conn_str)
        logging.info("Database connection established")
        return conn
    except Exception as e:
        logging.error(f"Database connection failed: {str(e)}")
        raise


def hash_password(password, salt=None):
    """Hash password with salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
    )
    return pwd_hash.hex(), salt


def verify_password(password, password_hash, salt):
    """Verify password against hash"""
    pwd_hash, _ = hash_password(password, salt)
    return pwd_hash == password_hash


def generate_session_token():
    """Generate secure session token"""
    return secrets.token_urlsafe(32)


def verify_session(session_token):
    """Verify session and return user_id"""
    if not session_token:
        return None

    try:
        from datetime import datetime

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT u.id
            FROM sessions s
            JOIN shopusers u ON s.user_id = u.id
            WHERE s.token = ? AND s.expires_at > ?
            """,
            (session_token, datetime.utcnow()),
        )
        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None
    except Exception as e:
        logging.error(f"Session verification error: {str(e)}")
        return None
