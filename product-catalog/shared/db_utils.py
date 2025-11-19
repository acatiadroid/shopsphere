import logging
import os
from datetime import datetime

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


def verify_session(session_token):
    """Verify session and return user_id"""
    if not session_token:
        return None

    try:
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


def verify_admin(session_token):
    """Verify if user is admin"""
    if not session_token:
        return False, None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT u.id, u.email
            FROM sessions s
            JOIN shopusers u ON s.user_id = u.id
            WHERE s.token = ? AND s.expires_at > ?
            """,
            (session_token, datetime.utcnow()),
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            user_id = result[0]
            email = result[1]
            is_admin = email == "admin@gmail.com"
            return is_admin, user_id
        return False, None
    except Exception as e:
        logging.error(f"Admin verification error: {str(e)}")
        return False, None
