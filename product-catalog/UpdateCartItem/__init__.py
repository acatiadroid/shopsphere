import json
import logging
import os
import sys
from datetime import datetime

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_session


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Update cart item quantity"""
    logging.info("Update cart item function triggered")

    cart_item_id = req.route_params.get("id")

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

    quantity = req_body.get("quantity")

    if not quantity or quantity < 1:
        return func.HttpResponse(
            json.dumps({"error": "Quantity must be at least 1"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT product_id FROM cart_items WHERE id = %s AND user_id = %s",
            (cart_item_id, user_id),
        )
        cart_item = cursor.fetchone()

        if not cart_item:
            cursor.close()
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Cart item not found"}),
                status_code=404,
                mimetype="application/json",
            )

        product_id = cart_item[0]

        cursor.execute(
            "SELECT stock_quantity FROM products WHERE id = %s", (product_id,)
        )
        product = cursor.fetchone()

        if not product or product[0] < quantity:
            cursor.close()
            conn.close()
            available = product[0] if product else 0
            return func.HttpResponse(
                json.dumps({"error": f"Not enough stock. Available: {available}"}),
                status_code=400,
                mimetype="application/json",
            )

        cursor.execute(
            "UPDATE cart_items SET quantity = %s WHERE id = %s",
            (quantity, cart_item_id),
        )
        conn.commit()
        cursor.close()
        conn.close()

        logging.info(f"Cart item {cart_item_id} updated to quantity {quantity}")
        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "cart_item_id": int(cart_item_id),
                    "quantity": quantity,
                    "message": "Cart updated",
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Update cart item error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
