import json
import logging

# Add parent directory to path to import shared modules
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
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
            """,
            (session_token,),
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
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
        import traceback

        error_details = traceback.format_exc()
        logging.error(f"Verify session error: {str(e)}")
        logging.error(f"Traceback: {error_details}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error", "details": str(e)}),
            status_code=500,
            mimetype="application/json",
        )
