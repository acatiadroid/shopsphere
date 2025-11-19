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
            SELECT w.id, w.product_id, w.added_at,
                   p.name, p.description, p.price, p.image_url, p.stock_quantity
            FROM wishlist w
            JOIN products p ON w.product_id = p.id
            WHERE w.user_id = ?
            ORDER BY w.added_at DESC
            """,
            (user_id,),
        )

        wishlist_items = []
        for row in cursor.fetchall():
            wishlist_items.append(
                {
                    "id": row[0],
                    "product_id": row[1],
                    "added_at": row[2].isoformat() if row[2] else None,
                    "product": {
                        "name": row[3],
                        "description": row[4],
                        "price": float(row[5]),
                        "image_url": row[6],
                        "stock_quantity": row[7],
                    },
                }
            )

        conn.close()

        return func.HttpResponse(
            json.dumps(
                {"wishlist_items": wishlist_items, "item_count": len(wishlist_items)}
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Get wishlist error: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
