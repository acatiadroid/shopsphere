import json
import logging
import os
import sys
from datetime import datetime

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_session


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Add item to shopping cart"""
    logging.info("Add to cart function triggered")

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
    quantity = req_body.get("quantity", 1)

    if not product_id:
        return func.HttpResponse(
            json.dumps({"error": "Product ID is required"}),
            status_code=400,
            mimetype="application/json",
        )

    if quantity < 1:
        return func.HttpResponse(
            json.dumps({"error": "Quantity must be at least 1"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, name, stock_quantity FROM products WHERE id = %s",
            (product_id,),
        )
        product = cursor.fetchone()

        if not product:
            cursor.close()
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Product not found"}),
                status_code=404,
                mimetype="application/json",
            )

        if product[2] < quantity:
            cursor.close()
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": f"Not enough stock. Available: {product[2]}"}),
                status_code=400,
                mimetype="application/json",
            )

        cursor.execute(
            "SELECT id, quantity FROM cart_items WHERE user_id = %s AND product_id = %s",
            (user_id, product_id),
        )
        existing = cursor.fetchone()

        if existing:
            new_quantity = existing[1] + quantity
            if new_quantity > product[2]:
                cursor.close()
                conn.close()
                return func.HttpResponse(
                    json.dumps({"error": f"Not enough stock. Available: {product[2]}"}),
                    status_code=400,
                    mimetype="application/json",
                )

            cursor.execute(
                "UPDATE cart_items SET quantity = %s WHERE id = %s",
                (new_quantity, existing[0]),
            )
            conn.commit()
            cursor.close()
            conn.close()

            return func.HttpResponse(
                json.dumps(
                    {
                        "success": True,
                        "cart_item_id": existing[0],
                        "quantity": new_quantity,
                        "message": "Cart updated",
                    }
                ),
                status_code=200,
                mimetype="application/json",
            )
        else:
            cursor.execute(
                "INSERT INTO cart_items (user_id, product_id, quantity, added_at) VALUES (%s, %s, %s, %s)",
                (user_id, product_id, quantity, datetime.utcnow()),
            )
            conn.commit()

            cart_item_id = cursor.lastrowid
            cursor.close()
            conn.close()

            return func.HttpResponse(
                json.dumps(
                    {
                        "success": True,
                        "cart_item_id": int(cart_item_id),
                        "product_id": product_id,
                        "quantity": quantity,
                        "message": "Product added to cart",
                    }
                ),
                status_code=201,
                mimetype="application/json",
            )

    except Exception as e:
        logging.error(f"Add to cart error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
