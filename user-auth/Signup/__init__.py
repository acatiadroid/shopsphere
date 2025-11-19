import json
import logging
import sys
from datetime import datetime, timedelta

import azure.functions as func

# Add parent directory to path to import shared modules
sys.path.append("..")
from shared.db_utils import generate_session_token, get_db_connection, hash_password


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Handle user signup"""
    logging.info("Signup function triggered")

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json",
        )

    email = req_body.get("email")
    password = req_body.get("password")
    name = req_body.get("name")

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
            conn.close()
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

        # Get the inserted user ID
        cursor.execute("SELECT @@IDENTITY AS id")
        user_id = int(cursor.fetchone()[0])

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
