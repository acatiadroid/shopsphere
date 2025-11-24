import logging
import os
from datetime import datetime

import mysql.connector


def get_db_connection():
    """Create database connection using mysql.connector"""
    conn_str = os.environ.get("SqlConnectionString")

    if not conn_str:
        raise ValueError("SqlConnectionString environment variable not set")

    try:
        # Parse the connection string (ODBC format to mysql.connector format)
        # Expected format: SERVER=host;PORT=port;DATABASE=db;UID=user;PWD=password
        params = {}
        for part in conn_str.split(";"):
            if "=" in part:
                key, value = part.split("=", 1)
                key = key.strip().upper()
                value = value.strip()

                if key == "SERVER":
                    params["host"] = value
                elif key == "PORT":
                    params["port"] = int(value)
                elif key == "DATABASE":
                    params["database"] = value
                elif key == "UID":
                    params["user"] = value
                elif key == "PWD":
                    params["password"] = value

        conn = mysql.connector.connect(**params)
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
            WHERE s.session_token = %s AND s.expires_at > %s
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
    """Verify session and check if user is admin. Returns (is_admin, user_id)"""
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
            WHERE s.session_token = %s AND s.expires_at > %s
            """,
            (session_token, datetime.utcnow()),
        )
        result = cursor.fetchone()
        conn.close()

        if not result:
            return False, None

        user_id, email = result
        is_admin = email == "admin@gmail.com"
        return is_admin, user_id
    except Exception as e:
        logging.error(f"Admin verification error: {str(e)}")
        return False, None
