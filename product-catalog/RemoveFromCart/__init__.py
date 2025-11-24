import json
import logging
import os
import sys

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_session


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Remove item from cart"""
    logging.info("Remove from cart function triggered")

    cart_item_id = req.route_params.get("id")

    session_token = req.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = verify_session(session_token)

    if not user_id:
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=401,
            mimetype="application/json",
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM cart_items WHERE id = %s AND user_id = %s",
            (cart_item_id, user_id),
        )
        conn.commit()

        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Cart item not found"}),
                status_code=404,
                mimetype="application/json",
            )

        cursor.close()
        conn.close()

        return func.HttpResponse(
            json.dumps({"success": True, "message": "Item removed from cart"}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Remove from cart error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
