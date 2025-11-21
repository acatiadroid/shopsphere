import json
import logging
import os
import sys

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_session


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Get user's shopping cart"""
    logging.info("Get cart function triggered")

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
            SELECT c.id, c.product_id, c.quantity, p.name, p.price, p.image_url, p.stock_quantity
            FROM cart_items c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
            """,
            (user_id,),
        )

        cart_items = []
        total = 0
        for row in cursor.fetchall():
            item_total = float(row[4]) * row[2]
            cart_items.append(
                {
                    "id": row[0],
                    "product_id": row[1],
                    "quantity": row[2],
                    "product": {
                        "name": row[3],
                        "price": float(row[4]),
                        "image_url": row[5],
                        "stock_quantity": row[6],
                    },
                    "item_total": item_total,
                }
            )
            total += item_total

        conn.close()

        return func.HttpResponse(
            json.dumps({"cart_items": cart_items, "total": total}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Get cart error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
