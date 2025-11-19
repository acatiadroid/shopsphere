import json
import logging
import os
import sys
from datetime import datetime

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Verify session token"""
    logging.info("Verify session function triggered")

    try:
        req_body = req.get_json()
        session_token = req_body.get("session_token")

        if not session_token:
            return func.HttpResponse(
                json.dumps({"success": False, "error": "Session token required"}),
                status_code=400,
                mimetype="application/json",
            )

        logging.info(f"Verifying session token")

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

        cursor.execute(
            """
            SELECT u.id, u.email, u.name, s.expires_at
            FROM sessions s
            JOIN shopusers u ON s.user_id = u.id
            WHERE s.token = ?
            """,
            (session_token,),
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
            logging.warning("Invalid session token")
            return func.HttpResponse(
                json.dumps({"valid": False, "error": "Invalid session"}),
                status_code=401,
                mimetype="application/json",
            )

        user_id, email, name, expires_at = result
        user_id = int(user_id)

        # Check if session expired
        if expires_at < datetime.utcnow():
            cursor.execute("DELETE FROM sessions WHERE token = ?", (session_token,))
            conn.commit()
            conn.close()
            logging.warning(f"Session expired for user: {email}")
            return func.HttpResponse(
                json.dumps({"valid": False, "error": "Session expired"}),
                status_code=401,
                mimetype="application/json",
            )

        conn.close()

        logging.info(f"Session verified for user: {email}")
        return func.HttpResponse(
            json.dumps(
                {
                    "valid": True,
                    "user": {
                        "id": user_id,
                        "email": email,
                        "name": name,
                        "is_admin": (email == "admin@gmail.com"),
                    },
                }
            ),
            status_code=200,
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
