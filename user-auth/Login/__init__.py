import json
import logging

# Add parent directory to path to import shared modules
import os
import sys
from datetime import datetime, timedelta

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import (
    generate_session_token,
    get_db_connection,
    verify_password,
)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Handle user login"""
    logging.info("Login function triggered")

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
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Invalid credentials"}),
                status_code=401,
                mimetype="application/json",
            )

        user_id, email, name, password_hash, salt = user
        user_id = int(user_id)

        # Verify password
        if not verify_password(password, password_hash, salt):
            conn.close()
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
        import traceback

        error_details = traceback.format_exc()
        logging.error(f"Login error: {str(e)}")
        logging.error(f"Traceback: {error_details}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error", "details": str(e)}),
            status_code=500,
            mimetype="application/json",
        )
