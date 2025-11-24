import json
import logging
import os
import sys

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection


def main(req: func.HttpRequest) -> func.HttpResponse:
    """User logout endpoint"""
    logging.info("Logout function triggered")

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
        logging.info("Processing logout request")

        try:
            conn = get_db_connection()
        except Exception as e:
            logging.error(f"Database connection failed: {str(e)}")
            return func.HttpResponse(
                json.dumps({"error": "Database connection failed"}),
                status_code=500,
                mimetype="application/json",
            )

        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE session_token = %s", (session_token,))
        conn.commit()
        cursor.close()
        conn.close()

        logging.info("Session deleted successfully")

    return func.HttpResponse(
        json.dumps({"success": True, "message": "Logged out successfully"}),
        status_code=200,
        mimetype="application/json",
    )
