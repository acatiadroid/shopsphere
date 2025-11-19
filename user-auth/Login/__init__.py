import json
import logging
import os
import sys
from datetime import datetime, timedelta

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import generate_session_token, get_db_connection, verify_password


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Handle user login"""
    logging.info("Login function triggered")

    try:
        req_body = req.get_json()
        email = req_body.get("email")
        password = req_body.get("password")

        if not email or not password:
            return func.HttpResponse(
                json.dumps({"success": False, "error": "Email and password required"}),
                status_code=400,
                mimetype="application/json",
            )

        logging.info(f"Attempting login for: {email}")

        # Connect to database
        try:
            conn = get_db_connection()
        except Exception as e:
            logging.error(f"Database connection failed: {str(e)}")
            return func.HttpResponse(
                json.dumps(
                    {"success": False, "error": f"Database connection error: {str(e)}"}
                ),
                status_code=500,
                mimetype="application/json",
            )

        cursor = conn.cursor()

        # Query user from shopusers table
        cursor.execute(
            "SELECT id, name, email, password, salt FROM shopusers WHERE email = ?",
            (email,),
        )
        user = cursor.fetchone()

        if not user:
            conn.close()
            logging.warning(f"User not found: {email}")
            return func.HttpResponse(
                json.dumps({"success": False, "error": "Invalid credentials"}),
                status_code=401,
                mimetype="application/json",
            )

        user_id, name, user_email, password_hash, salt = user
        user_id = int(user_id)

        # Verify password if salt exists
        if salt:
            if not verify_password(password, password_hash, salt):
                conn.close()
                logging.warning(f"Invalid password for: {email}")
                return func.HttpResponse(
                    json.dumps({"success": False, "error": "Invalid credentials"}),
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

        # Return user data
        user_data = {
            "success": True,
            "user": {
                "id": user_id,
                "name": name,
                "email": user_email,
                "is_admin": (user_email == "admin@gmail.com"),
            },
            "session_token": session_token,
            "hashed_password": password_hash,
        }

        logging.info(f"Login successful for: {email}")
        return func.HttpResponse(
            json.dumps(user_data), status_code=200, mimetype="application/json"
        )

    except ValueError:
        logging.error("Invalid JSON in request")
        return func.HttpResponse(
            json.dumps({"success": False, "error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json",
        )
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"success": False, "error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )
