import json
import logging
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
    """User login endpoint"""
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
        logging.info(f"Attempting login for: {email}")

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

        cursor.execute(
            "SELECT id, name, email, password, salt FROM shopusers WHERE email = %s",
            (email,),
        )

        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            logging.warning(f"Login failed: User not found for email {email}")
            return func.HttpResponse(
                json.dumps({"error": "Invalid credentials"}),
                status_code=401,
                mimetype="application/json",
            )

        user_id, name, user_email, password_hash, salt = user
        user_id = int(user_id)

        if salt:
            if not verify_password(password, password_hash, salt):
                cursor.close()
                conn.close()
                logging.warning(f"Login failed: Invalid password for {email}")
                return func.HttpResponse(
                    json.dumps({"error": "Invalid credentials"}),
                    status_code=401,
                    mimetype="application/json",
                )

        session_token = generate_session_token()
        expires_at = datetime.utcnow() + timedelta(days=7)

        cursor.execute(
            "INSERT INTO sessions (user_id, session_token, expires_at) VALUES (%s, %s, %s)",
            (user_id, session_token, expires_at),
        )
        conn.commit()
        cursor.close()
        conn.close()

        user_data = {
            "success": True,
            "session_token": session_token,
            "user": {"id": user_id, "name": name, "email": user_email},
        }

        logging.info(f"Login successful for user {user_id}")
        return func.HttpResponse(
            json.dumps(user_data), status_code=200, mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
