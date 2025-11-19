import json
import logging
import sys

import azure.functions as func

# Add parent directory to path to import shared modules
sys.path.append("..")
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
        logging.error(f"Logout error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
