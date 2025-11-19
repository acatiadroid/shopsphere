import json
import logging
import os
import sys

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_session


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Track order delivery status"""
    logging.info("Track order function triggered")

    order_id = req.route_params.get("id")

    # Verify session
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
            """
            SELECT status, tracking_number, created_at, paid_at, shipped_at, delivered_at
            FROM orders
            WHERE id = ? AND user_id = ?
            """,
            (order_id, user_id),
        )
        order = cursor.fetchone()

        if not order:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Order not found"}),
                status_code=404,
                mimetype="application/json",
            )

        conn.close()

        tracking_info = {
            "order_id": int(order_id),
            "status": order[0],
            "tracking_number": order[1],
            "timeline": {
                "ordered": order[2].isoformat() if order[2] else None,
                "paid": order[3].isoformat() if order[3] else None,
                "shipped": order[4].isoformat() if order[4] else None,
                "delivered": order[5].isoformat() if order[5] else None,
            },
        }

        return func.HttpResponse(
            json.dumps(tracking_info),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Track order error: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
