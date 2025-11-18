import hashlib
import json
import logging
import os
import secrets
from datetime import datetime, timedelta

import azure.functions as func
import pyodbc

app = func.FunctionApp()

# Database connection string.
db_conn = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=luke-shopsphere.database.windows.net;DATABASE=luke-database;UID=myadmin;PWD=Abcdefgh0!;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

def get_db_connection():
    """Create database connection"""
    return pyodbc.connect(db_conn)

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


@app.function_name(name="UserAuth")
@app.route(route="auth/{action}", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def user_auth(req: func.HttpRequest) -> func.HttpResponse:
    """Handle user authentication"""
    logging.info("User auth function triggered")

    action = req.route_params.get("action")

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json",
        )

    if action == "signup":
        return handle_signup(req_body)
    elif action == "login":
        return handle_login(req_body)
    elif action == "logout":
        return handle_logout(req_body)
    elif action == "verify":
        return handle_verify_session(req_body)
    else:
        return func.HttpResponse(
            json.dumps({"error": "Invalid action"}),
            status_code=400,
            mimetype="application/json",
        )


def handle_signup(data):
    """Handle user signup"""
    email = data.get("email")
    password = data.get("password")
    name = data.get("name")

    if not email or not password or not name:
        return func.HttpResponse(
            json.dumps({"error": "Email, password, and name are required"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return func.HttpResponse(
                json.dumps({"error": "User already exists"}),
                status_code=409,
                mimetype="application/json",
            )

        # Hash password
        password_hash, salt = hash_password(password)

        # Create user
        cursor.execute(
            "INSERT INTO users (email, password_hash, salt, name, created_at) VALUES (?, ?, ?, ?, ?)",
            (email, password_hash, salt, name, datetime.utcnow()),
        )
        conn.commit()

        user_id = cursor.execute("SELECT @@IDENTITY").fetchone()[0]

        # Create session
        session_token = generate_session_token()
        expires_at = datetime.utcnow() + timedelta(days=7)

        cursor.execute(
            "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
            (user_id, session_token, expires_at),
        )
        conn.commit()

        conn.close()

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "user_id": user_id,
                    "email": email,
                    "name": name,
                    "session_token": session_token,
                }
            ),
            status_code=201,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Signup error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


def handle_login(data):
    """Handle user login"""
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return func.HttpResponse(
            json.dumps({"error": "Email and password are required"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get user
        cursor.execute(
            "SELECT id, email, name, password_hash, salt FROM users WHERE email = ?",
            (email,),
        )
        user = cursor.fetchone()

        if not user:
            return func.HttpResponse(
                json.dumps({"error": "Invalid credentials"}),
                status_code=401,
                mimetype="application/json",
            )

        user_id, email, name, password_hash, salt = user

        # Verify password
        if not verify_password(password, password_hash, salt):
            return func.HttpResponse(
                json.dumps({"error": "Invalid credentials"}),
                status_code=401,
                mimetype="application/json",
            )

        # Create session
        session_token = generate_session_token()
        expires_at = datetime.utcnow() + timedelta(days=7)

        cursor.execute(
            "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
            (user_id, session_token, expires_at),
        )
        conn.commit()
        conn.close()

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "user_id": user_id,
                    "email": email,
                    "name": name,
                    "session_token": session_token,
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


def handle_logout(data):
    """Handle user logout"""
    session_token = data.get("session_token")

    if not session_token:
        return func.HttpResponse(
            json.dumps({"error": "Session token required"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM sessions WHERE token = ?", (session_token,))
        conn.commit()
        conn.close()

        return func.HttpResponse(
            json.dumps({"success": True}), status_code=200, mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Logout error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


def handle_verify_session(data):
    """Verify session token"""
    session_token = data.get("session_token")

    if not session_token:
        return func.HttpResponse(
            json.dumps({"error": "Session token required"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT u.id, u.email, u.name, s.expires_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
            """,
            (session_token,),
        )
        result = cursor.fetchone()

        if not result:
            return func.HttpResponse(
                json.dumps({"valid": False, "error": "Invalid session"}),
                status_code=401,
                mimetype="application/json",
            )

        user_id, email, name, expires_at = result

        # Check if session expired
        if expires_at < datetime.utcnow():
            cursor.execute("DELETE FROM sessions WHERE token = ?", (session_token,))
            conn.commit()
            conn.close()
            return func.HttpResponse(
                json.dumps({"valid": False, "error": "Session expired"}),
                status_code=401,
                mimetype="application/json",
            )

        conn.close()

        return func.HttpResponse(
            json.dumps(
                {"valid": True, "user_id": user_id, "email": email, "name": name}
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Verify session error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
