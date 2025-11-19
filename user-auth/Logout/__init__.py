import json
import logging

# Add parent directory to path to import shared modules
import os
import sys

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Handle user logout"""
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
        return func.HttpResponse(
            json.dumps({"error": "Session token required"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM sessions WHERE token = ?", (session_token,))
        conn.commit()
        conn.close()

        return func.HttpResponse(
            json.dumps({"success": True}), status_code=200, mimetype="application/json"
        )

    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        logging.error(f"Logout error: {str(e)}")
        logging.error(f"Traceback: {error_details}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error", "details": str(e)}),
            status_code=500,
            mimetype="application/json",
        )
