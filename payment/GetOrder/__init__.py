import json
import logging
import os
import sys
from decimal import Decimal

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_session


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Get order details with items."""
    logging.info("Get order function triggered")

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
            SELECT id, total_amount, status, shipping_address, tracking_number,
                   created_at, paid_at, shipped_at, delivered_at
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

        cursor.execute(
            """
            SELECT oi.id, oi.product_id, oi.quantity, oi.price_at_purchase,
                   p.name, p.image_url
            FROM order_items oi
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
            """,
            (order_id,),
        )
        items = cursor.fetchall()

        conn.close()

        order_dict = {
            "id": order[0],
            "total_amount": float(order[1])
            if isinstance(order[1], Decimal)
            else order[1],
            "status": order[2],
            "shipping_address": order[3],
            "tracking_number": order[4],
            "created_at": order[5].isoformat() if order[5] else None,
            "paid_at": order[6].isoformat() if order[6] else None,
            "shipped_at": order[7].isoformat() if order[7] else None,
            "delivered_at": order[8].isoformat() if order[8] else None,
        }

        items_list = []
        for item in items:
            item_total = (
                float(item[3]) * item[2]
                if isinstance(item[3], Decimal)
                else item[3] * item[2]
            )
            items_list.append(
                {
                    "id": item[0],
                    "product_id": item[1],
                    "quantity": item[2],
                    "price_at_purchase": float(item[3])
                    if isinstance(item[3], Decimal)
                    else item[3],
                    "item_total": item_total,
                    "product": {
                        "name": item[4],
                        "image_url": item[5],
                    },
                }
            )

        order_dict["items"] = items_list

        return func.HttpResponse(
            json.dumps(order_dict),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Get order error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
