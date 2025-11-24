import json
import logging
import os
import sys
from datetime import datetime

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Verify session token endpoint"""
    logging.info("Verify session function triggered")

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json",
        )

    session_token = req_body.get("session_token")

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
            JOIN shopusers u ON s.user_id = u.id
            WHERE s.session_token = %s
            """,
            (session_token,),
        )
        result = cursor.fetchone()

        if not result:
            cursor.close()
            conn.close()
            logging.warning("Invalid session token")
            return func.HttpResponse(
                json.dumps({"valid": False, "error": "Invalid session"}),
                status_code=401,
                mimetype="application/json",
            )

        user_id, email, name, expires_at = result
        user_id = int(user_id)

        if expires_at < datetime.utcnow():
            cursor.execute(
                "DELETE FROM sessions WHERE session_token = %s", (session_token,)
            )
            conn.commit()
            cursor.close()
            conn.close()
            logging.warning(f"Session expired for user {email}")
            return func.HttpResponse(
                json.dumps({"valid": False, "error": "Session expired"}),
                status_code=401,
                mimetype="application/json",
            )

        cursor.close()
        conn.close()

        logging.info(f"Session verified for user {user_id}")
        return func.HttpResponse(
            json.dumps(
                {
                    "valid": True,
                    "user": {
                        "id": user_id,
                        "email": email,
                        "name": name,
                    },
                }
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
