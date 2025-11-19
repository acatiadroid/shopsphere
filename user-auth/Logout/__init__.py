import json
import logging
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
        session_token = req_body.get("session_token")

        if not session_token:
            return func.HttpResponse(
                json.dumps({"success": False, "error": "Session token required"}),
                status_code=400,
                mimetype="application/json",
            )

        logging.info("Processing logout request")

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

        # Delete session
        cursor.execute("DELETE FROM sessions WHERE token = ?", (session_token,))
        conn.commit()
        conn.close()

        logging.info("Logout successful")
        return func.HttpResponse(
            json.dumps({"success": True}), status_code=200, mimetype="application/json"
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
