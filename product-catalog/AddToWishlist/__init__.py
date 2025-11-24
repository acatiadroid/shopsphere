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

        cursor.execute("SELECT id, name FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()

        if not product:
            cursor.close()
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Product not found"}),
                status_code=404,
                mimetype="application/json",
            )

        cursor.execute(
            "SELECT id FROM wishlist WHERE user_id = %s AND product_id = %s",
            (user_id, product_id),
        )

        if cursor.fetchone():
            cursor.close()
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Product already in wishlist"}),
                status_code=400,
                mimetype="application/json",
            )

        cursor.execute(
            "INSERT INTO wishlist (user_id, product_id, added_at) VALUES (%s, %s, %s)",
            (user_id, product_id, datetime.utcnow()),
        )
        conn.commit()

        wishlist_id = cursor.lastrowid

        cursor.close()
        conn.close()

        logging.info(f"Product {product_id} added to wishlist for user {user_id}")
        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "wishlist_id": int(wishlist_id),
                    "product_id": product_id,
                    "message": "Product added to wishlist",
                }
            ),
            status_code=201,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Add to wishlist error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
