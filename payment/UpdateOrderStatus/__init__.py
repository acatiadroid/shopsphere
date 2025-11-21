import json
import logging
import os
import sys
from datetime import datetime

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_admin


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Update order status (admin only)"""
    logging.info("Update order status function triggered")

    order_id = req.route_params.get("id")

    session_token = req.headers.get("Authorization", "").replace("Bearer ", "")
    is_admin, user_id = verify_admin(session_token)

    if not is_admin:
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=403,
            mimetype="application/json",
        )

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json",
        )

    status = req_body.get("status")
    tracking_number = req_body.get("tracking_number")

    valid_statuses = ["pending", "paid", "shipped", "delivered", "cancelled"]
    if status and status not in valid_statuses:
        return func.HttpResponse(
            json.dumps(
                {
                    "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                }
            ),
            status_code=400,
            mimetype="application/json",
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, status FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()

        if not order:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Order not found"}),
                status_code=404,
                mimetype="application/json",
            )

        update_fields = []
        params = []

        if status:
            update_fields.append("status = ?")
            params.append(status)

            if status == "shipped" and order[1] != "shipped":
                update_fields.append("shipped_at = ?")
                params.append(datetime.utcnow())

            if status == "delivered" and order[1] != "delivered":
                update_fields.append("delivered_at = ?")
                params.append(datetime.utcnow())

        if tracking_number:
            update_fields.append("tracking_number = ?")
            params.append(tracking_number)

        if not update_fields:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "No fields to update"}),
                status_code=400,
                mimetype="application/json",
            )

        params.append(order_id)
        query = f"UPDATE orders SET {', '.join(update_fields)} WHERE id = ?"

        cursor.execute(query, tuple(params))
        conn.commit()
        conn.close()

        logging.info(f"Order {order_id} updated successfully")
        return func.HttpResponse(
            json.dumps({"success": True, "message": "Order updated successfully"}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Update order status error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
