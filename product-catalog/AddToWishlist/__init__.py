import json
import logging
import os
import sys
from datetime import datetime

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_session


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Add item to wishlist."""
    logging.info("Add to wishlist function triggered")

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
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json",
        )

    product_id = req_body.get("product_id")

    if not product_id:
        return func.HttpResponse(
            json.dumps({"error": "Product ID is required"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if product exists
        cursor.execute("SELECT id, name FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()

        if not product:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Product not found"}),
                status_code=404,
                mimetype="application/json",
            )

        # Check if already in wishlist
        cursor.execute(
            "SELECT id FROM wishlist WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        existing = cursor.fetchone()

        if existing:
            conn.close()
            return func.HttpResponse(
                json.dumps(
                    {
                        "success": True,
                        "message": "Product already in wishlist",
                        "wishlist_item_id": existing[0],
                    }
                ),
                status_code=200,
                mimetype="application/json",
            )

        # Add to wishlist
        cursor.execute(
            "INSERT INTO wishlist (user_id, product_id, added_at) VALUES (?, ?, ?)",
            (user_id, product_id, datetime.utcnow()),
        )
        conn.commit()

        wishlist_item_id = cursor.execute("SELECT @@IDENTITY").fetchone()[0]
        conn.close()

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "message": "Item added to wishlist",
                    "wishlist_item_id": int(wishlist_item_id),
                }
            ),
            status_code=201,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Add to wishlist error: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
