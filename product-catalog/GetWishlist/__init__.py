import json
import logging
import os
import sys

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_session


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Get user's wishlist"""
    logging.info("Get wishlist function triggered")

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
            SELECT w.id, w.product_id, p.name, p.price, p.image_url, p.stock_quantity
            FROM wishlist w
            JOIN products p ON w.product_id = p.id
            WHERE w.user_id = %s
            """,
            (user_id,),
        )

        wishlist_items = []
        for row in cursor.fetchall():
            wishlist_items.append(
                {
                    "id": row[0],
                    "product_id": row[1],
                    "product": {
                        "name": row[2],
                        "price": float(row[3]),
                        "image_url": row[4],
                        "stock_quantity": row[5],
                    },
                }
            )

        cursor.close()
        conn.close()

        return func.HttpResponse(
            json.dumps({"wishlist_items": wishlist_items}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Get wishlist error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
