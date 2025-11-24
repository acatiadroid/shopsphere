import json
import logging
import os
import sys

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_session


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Track order status and shipment"""
    logging.info("Track order function triggered")

    order_id = req.route_params.get("id")

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
            SELECT id, status, tracking_number, created_at, paid_at, shipped_at, delivered_at
            FROM orders
            WHERE id = %s AND user_id = %s
            """,
            (order_id, user_id),
        )

        order = cursor.fetchone()

        if not order:
            cursor.close()
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Order not found"}),
                status_code=404,
                mimetype="application/json",
            )

        cursor.close()
        conn.close()

        tracking = {
            "order_id": order[0],
            "status": order[1],
            "tracking_number": order[2],
            "created_at": order[3].isoformat() if order[3] else None,
            "paid_at": order[4].isoformat() if order[4] else None,
            "shipped_at": order[5].isoformat() if order[5] else None,
            "delivered_at": order[6].isoformat() if order[6] else None,
        }

        status_history = []
        if order[3]:
            status_history.append(
                {"status": "pending", "timestamp": order[3].isoformat()}
            )
        if order[4]:
            status_history.append({"status": "paid", "timestamp": order[4].isoformat()})
        if order[5]:
            status_history.append(
                {"status": "shipped", "timestamp": order[5].isoformat()}
            )
        if order[6]:
            status_history.append(
                {"status": "delivered", "timestamp": order[6].isoformat()}
            )

        tracking["status_history"] = status_history

        return func.HttpResponse(
            json.dumps({"tracking": tracking}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Track order error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
