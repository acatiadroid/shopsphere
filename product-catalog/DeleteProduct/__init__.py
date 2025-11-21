import json
import logging
import os
import sys

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_admin


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Delete product (admin only)"""
    logging.info("Delete product function triggered")

    product_id = req.route_params.get("id")

    session_token = req.headers.get("Authorization", "").replace("Bearer ", "")
    is_admin, user_id = verify_admin(session_token)

    if not is_admin:
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=403,
            mimetype="application/json",
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()

        if cursor.rowcount == 0:
            return func.HttpResponse(
                json.dumps({"error": "Product not found"}),
                status_code=404,
                mimetype="application/json",
            )

        conn.close()

        return func.HttpResponse(
            json.dumps({"success": True}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Delete product error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
