import json
import logging
import os
import sys
from datetime import datetime

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_session


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Convert cart to order"""
    logging.info("Checkout function triggered")

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

    shipping_address = req_body.get("shipping_address")

    if not shipping_address:
        return func.HttpResponse(
            json.dumps({"error": "Shipping address is required"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get cart items
        cursor.execute(
            """
            SELECT c.product_id, c.quantity, p.price, p.stock_quantity, p.name
            FROM cart_items c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
            """,
            (user_id,),
        )
        cart_items = cursor.fetchall()

        if not cart_items:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Cart is empty"}),
                status_code=400,
                mimetype="application/json",
            )

        # Calculate total and verify stock
        total_amount = 0
        order_items = []
        for item in cart_items:
            product_id, quantity, price, stock, name = item
            if stock < quantity:
                conn.close()
                return func.HttpResponse(
                    json.dumps(
                        {"error": f"Insufficient stock for {name}. Available: {stock}"}
                    ),
                    status_code=400,
                    mimetype="application/json",
                )
            item_total = float(price) * quantity
            total_amount += item_total
            order_items.append(
                {
                    "product_id": product_id,
                    "quantity": quantity,
                    "price": float(price),
                }
            )

        # Create order
        cursor.execute(
            """
            INSERT INTO orders (user_id, total_amount, status, shipping_address, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, total_amount, "pending", shipping_address, datetime.utcnow()),
        )
        conn.commit()

        order_id = cursor.execute("SELECT @@IDENTITY").fetchone()[0]

        # Create order items and update stock
        for item in order_items:
            cursor.execute(
                """
                INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase)
                VALUES (?, ?, ?, ?)
                """,
                (order_id, item["product_id"], item["quantity"], item["price"]),
            )

            # Update product stock
            cursor.execute(
                "UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?",
                (item["quantity"], item["product_id"]),
            )

        # Clear cart
        cursor.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))

        conn.commit()
        conn.close()

        logging.info(f"Order {order_id} created for user {user_id}")
        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "order_id": int(order_id),
                    "total_amount": total_amount,
                    "status": "pending",
                    "message": "Order created successfully. Please proceed to payment.",
                }
            ),
            status_code=201,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Checkout error: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
