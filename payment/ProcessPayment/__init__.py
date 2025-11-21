import json
import logging
import os
import random
import sys
import uuid
from datetime import datetime

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_session


def generate_transaction_id():
    """Generate a unique transaction ID"""
    return f"TXN-{uuid.uuid4().hex[:12].upper()}"


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Process virtual payment"""
    logging.info("Process payment function triggered")

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
    payment_method = req_body.get("payment_method", "credit_card")

    if not order_id or not amount:
        return func.HttpResponse(
            json.dumps({"error": "Order ID and amount are required"}),
            status_code=400,
            mimetype="application/json",
        )

    valid_methods = ["credit_card", "debit_card", "paypal", "apple_pay", "google_pay"]
    if payment_method not in valid_methods:
        return func.HttpResponse(
            json.dumps(
                {
                    "error": f"Invalid payment method. Must be one of: {', '.join(valid_methods)}"
                }
            ),
            status_code=400,
            mimetype="application/json",
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, total_amount, status FROM orders WHERE id = ? AND user_id = ?",
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

        order_id_db, total_amount, order_status = order

        if order_status == "paid":
            return func.HttpResponse(
                json.dumps({"error": "Order is already paid"}),
                status_code=400,
                mimetype="application/json",
            )

        if abs(float(amount) - float(total_amount)) > 0.01:
            return func.HttpResponse(
                json.dumps({"error": "Amount does not match order total"}),
                status_code=400,
                mimetype="application/json",
            )

        transaction_id = generate_transaction_id()

        payment_successful = random.random() < 0.95

        if not payment_successful:
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
                        "error": "Payment declined. Please try again or use a different payment method.",
                        "transaction_id": transaction_id,
                    }
                ),
                status_code=402,
                mimetype="application/json",
            )

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

        cursor.execute(
            "UPDATE orders SET status = ?, paid_at = ? WHERE id = ?",
            ("paid", datetime.utcnow(), order_id),
        )

        conn.commit()
        conn.close()

        logging.info(f"Payment processed successfully for order {order_id}")
        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "transaction_id": transaction_id,
                    "order_id": int(order_id),
                    "amount": float(amount),
                    "payment_method": payment_method,
                    "message": "Payment processed successfully",
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
