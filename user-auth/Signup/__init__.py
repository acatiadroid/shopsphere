import json
import logging
import os
import sys
from datetime import datetime, timedelta

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import generate_session_token, get_db_connection, hash_password


def main(req: func.HttpRequest) -> func.HttpResponse:
    """User signup endpoint"""
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
        logging.info(f"Attempting signup for: {email}")

        try:
            conn = get_db_connection()
        except Exception as conn_err:
            logging.error(f"Database connection failed: {str(conn_err)}")
            return func.HttpResponse(
                json.dumps({"error": "Database connection failed"}),
                status_code=500,
                mimetype="application/json",
            )

        cursor = conn.cursor()

        cursor.execute("SELECT id FROM shopusers WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            logging.warning(f"Signup failed: User already exists for email {email}")
            return func.HttpResponse(
                json.dumps({"error": "User already exists"}),
                status_code=409,
                mimetype="application/json",
            )

        password_hash, salt = hash_password(password)

        cursor.execute(
            "INSERT INTO shopusers (email, password, salt, name, created_at) VALUES (%s, %s, %s, %s, %s)",
            (email, password_hash, salt, name, datetime.utcnow()),
        )
        conn.commit()

        user_id = cursor.lastrowid

        session_token = generate_session_token()
        expires_at = datetime.utcnow() + timedelta(days=7)

        cursor.execute(
            "INSERT INTO sessions (user_id, session_token, expires_at) VALUES (%s, %s, %s)",
            (user_id, session_token, expires_at),
        )
        conn.commit()
        cursor.close()
        conn.close()

        logging.info(f"Signup successful for user {user_id}")
        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "session_token": session_token,
                    "user": {
                        "id": user_id,
                        "email": email,
                        "name": name,
                    },
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
