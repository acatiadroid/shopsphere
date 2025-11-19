import json
import logging
import os
import sys
from datetime import datetime, timedelta

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import generate_session_token, get_db_connection, hash_password


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Handle user signup"""
    logging.info("Signup function triggered")

    try:
        req_body = req.get_json()
        email = req_body.get("email")
        password = req_body.get("password")
        name = req_body.get("name")

        if not email or not password or not name:
            return func.HttpResponse(
                json.dumps(
                    {
                        "success": False,
                        "error": "Email, password, and name are required",
                    }
                ),
                status_code=400,
                mimetype="application/json",
            )

        logging.info(f"Attempting signup for: {email}")

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

        # Check if user exists in shopusers table
        cursor.execute("SELECT id FROM shopusers WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            logging.warning(f"User already exists: {email}")
            return func.HttpResponse(
                json.dumps({"success": False, "error": "User already exists"}),
                status_code=409,
                mimetype="application/json",
            )

        # Hash password
        password_hash, salt = hash_password(password)

        # Create user in shopusers table
        cursor.execute(
            "INSERT INTO shopusers (email, password, salt, name, created_at) VALUES (?, ?, ?, ?, ?)",
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

        logging.info(f"Signup successful for: {email}")
        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "user": {
                        "id": user_id,
                        "email": email,
                        "name": name,
                        "is_admin": (email == "admin@gmail.com"),
                    },
                    "session_token": session_token,
                }
            ),
            status_code=201,
            mimetype="application/json",
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
