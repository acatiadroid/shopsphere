import json
import logging
import os
import sys
from datetime import datetime

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import generate_transaction_id, get_db_connection, verify_session


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Process virtual payment"""
    logging.info("Process payment function triggered")

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

    order_id = req_body.get("order_id")
    amount = req_body.get("amount")
    payment_method = req_body.get(
        "payment_method"
    )  # credit_card, debit_card, paypal, etc.
    card_details = req_body.get("card_details", {})

    if not order_id or not amount or not payment_method:
        return func.HttpResponse(
            json.dumps({"error": "Order ID, amount, and payment method are required"}),
            status_code=400,
            mimetype="application/json",
        )

    # Validate payment method
    valid_methods = ["credit_card", "debit_card", "paypal", "apple_pay", "google_pay"]
    if payment_method not in valid_methods:
        return func.HttpResponse(
            json.dumps(
                {
                    "error": f"Invalid payment method. Valid methods: {', '.join(valid_methods)}"
                }
            ),
            status_code=400,
            mimetype="application/json",
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verify order exists and belongs to user
        cursor.execute(
            "SELECT id, total_amount, status FROM orders WHERE id = ? AND user_id = ?",
            (order_id, user_id),
        )
        order = cursor.fetchone()

        if not order:
            return func.HttpResponse(
                json.dumps({"error": "Order not found"}),
                status_code=404,
                mimetype="application/json",
            )

        order_id_db, total_amount, order_status = order

        # Check if order is already paid
        if order_status == "paid":
            return func.HttpResponse(
                json.dumps({"error": "Order already paid"}),
                status_code=400,
                mimetype="application/json",
            )

        # Validate amount
        if abs(float(amount) - float(total_amount)) > 0.01:
            return func.HttpResponse(
                json.dumps({"error": "Payment amount does not match order total"}),
                status_code=400,
                mimetype="application/json",
            )

        # Simulate payment processing
        # In a real system, this would integrate with Stripe, PayPal, etc.
        transaction_id = generate_transaction_id()

        # Simulate success/failure (95% success rate for demo)
        import random

        payment_successful = random.random() < 0.95

        if not payment_successful:
            # Record failed transaction
            cursor.execute(
                """
                INSERT INTO transactions (order_id, user_id, amount, payment_method, status, transaction_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    user_id,
                    amount,
                    payment_method,
                    "failed",
                    transaction_id,
                    datetime.utcnow(),
                ),
            )
            conn.commit()
            conn.close()

            return func.HttpResponse(
                json.dumps(
                    {
                        "success": False,
                        "error": "Payment processing failed. Please try again.",
                        "transaction_id": transaction_id,
                    }
                ),
                status_code=402,
                mimetype="application/json",
            )

        # Record successful transaction
        cursor.execute(
            """
            INSERT INTO transactions (order_id, user_id, amount, payment_method, status, transaction_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                user_id,
                amount,
                payment_method,
                "completed",
                transaction_id,
                datetime.utcnow(),
            ),
        )

        # Update order status
        cursor.execute(
            "UPDATE orders SET status = ?, paid_at = ? WHERE id = ?",
            ("paid", datetime.utcnow(), order_id),
        )

        conn.commit()
        conn.close()

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "transaction_id": transaction_id,
                    "order_id": order_id,
                    "amount": float(amount),
                    "payment_method": payment_method,
                    "status": "completed",
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Process payment error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
