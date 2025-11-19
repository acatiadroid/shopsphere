import json
import logging
import os
import sys

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_session


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Get order details with items"""
    logging.info("Get order function triggered")

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

        # Get order
        cursor.execute(
            """
            SELECT id, total_amount, status, shipping_address, tracking_number,
                   created_at, paid_at, shipped_at, delivered_at
            FROM orders
            WHERE id = ? AND user_id = ?
            """,
            (order_id, user_id),
        )
        order_row = cursor.fetchone()

        if not order_row:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Order not found"}),
                status_code=404,
                mimetype="application/json",
            )

        # Get order items
        cursor.execute(
            """
            SELECT oi.id, oi.product_id, oi.quantity, oi.price_at_purchase,
                   p.name, p.description, p.image_url
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
            """,
            (order_id,),
        )

        items = []
        for item_row in cursor.fetchall():
            items.append(
                {
                    "id": item_row[0],
                    "product_id": item_row[1],
                    "quantity": item_row[2],
                    "price_at_purchase": float(item_row[3]),
                    "product": {
                        "name": item_row[4],
                        "description": item_row[5],
                        "image_url": item_row[6],
                    },
                    "item_total": float(item_row[3]) * item_row[2],
                }
            )

        conn.close()

        order = {
            "id": order_row[0],
            "total_amount": float(order_row[1]),
            "status": order_row[2],
            "shipping_address": order_row[3],
            "tracking_number": order_row[4],
            "created_at": order_row[5].isoformat() if order_row[5] else None,
            "paid_at": order_row[6].isoformat() if order_row[6] else None,
            "shipped_at": order_row[7].isoformat() if order_row[7] else None,
            "delivered_at": order_row[8].isoformat() if order_row[8] else None,
            "items": items,
        }

        return func.HttpResponse(
            json.dumps(order), status_code=200, mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Get order error: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
