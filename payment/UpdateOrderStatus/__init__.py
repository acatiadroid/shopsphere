import json
import logging
import os
import sys
from datetime import datetime

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_session


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Update order status (admin only)"""
    logging.info("Update order status function triggered")

    order_id = req.route_params.get("id")

    # Verify admin
    session_token = req.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = verify_session(session_token)

    if not user_id:
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=401,
            mimetype="application/json",
        )

    # Check if admin
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT email FROM shopusers WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if not user or user[0] != "admin@gmail.com":
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Forbidden - Admin access required"}),
                status_code=403,
                mimetype="application/json",
            )

        # Get request body
        try:
            req_body = req.get_json()
        except ValueError:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON"}),
                status_code=400,
                mimetype="application/json",
            )

        status = req_body.get("status")
        tracking_number = req_body.get("tracking_number")

        valid_statuses = [
            "pending",
            "paid",
            "processing",
            "shipped",
            "delivered",
            "cancelled",
        ]
        if status and status not in valid_statuses:
            conn.close()
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": f"Invalid status. Valid statuses: {', '.join(valid_statuses)}"
                    }
                ),
                status_code=400,
                mimetype="application/json",
            )

        # Build update query
        updates = []
        params = []

        if status:
            updates.append("status = ?")
            params.append(status)

            # Set timestamps based on status
            if status == "shipped":
                updates.append("shipped_at = ?")
                params.append(datetime.utcnow())
            elif status == "delivered":
                updates.append("delivered_at = ?")
                params.append(datetime.utcnow())

        if tracking_number:
            updates.append("tracking_number = ?")
            params.append(tracking_number)

        if not updates:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "No fields to update"}),
                status_code=400,
                mimetype="application/json",
            )

        params.append(order_id)
        query = f"UPDATE orders SET {', '.join(updates)} WHERE id = ?"

        cursor.execute(query, params)
        conn.commit()

        if cursor.rowcount == 0:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Order not found"}),
                status_code=404,
                mimetype="application/json",
            )

        conn.close()

        logging.info(f"Order {order_id} status updated to {status}")
        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "order_id": int(order_id),
                    "status": status,
                    "tracking_number": tracking_number,
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Update order status error: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
