import json
import logging
import os
import secrets
from datetime import datetime
from decimal import Decimal

import azure.functions as func
import pyodbc

app = func.FunctionApp()


def get_db_connection():
    """Create database connection"""
    conn_str = os.environ.get("SqlConnectionString")
    return pyodbc.connect(conn_str, autocommit=False)


def verify_session(session_token):
    """Verify session and return user_id"""
    if not session_token:
        return None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT u.id
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ? AND s.expires_at > ?
            """,
            (session_token, datetime.utcnow()),
        )
        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None
    except Exception as e:
        logging.error(f"Session verification error: {str(e)}")
        return None


def generate_transaction_id():
    """Generate unique transaction ID"""
    return f"TXN-{secrets.token_hex(8).upper()}"


@app.function_name(name="ProcessPayment")
@app.route(
    route="payment/process", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS
)
def process_payment(req: func.HttpRequest) -> func.HttpResponse:
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


@app.function_name(name="GetTransactions")
@app.route(
    route="payment/transactions", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS
)
def get_transactions(req: func.HttpRequest) -> func.HttpResponse:
    """Get user's transaction history"""
    logging.info("Get transactions function triggered")

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
            SELECT id, order_id, amount, payment_method, status, transaction_id, created_at
            FROM transactions
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        )

        transactions = []
        for row in cursor.fetchall():
            transactions.append(
                {
                    "id": row[0],
                    "order_id": row[1],
                    "amount": float(row[2]),
                    "payment_method": row[3],
                    "status": row[4],
                    "transaction_id": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                }
            )

        conn.close()

        return func.HttpResponse(
            json.dumps({"transactions": transactions}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Get transactions error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


@app.function_name(name="GetTransaction")
@app.route(
    route="payment/transactions/{id}",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def get_transaction(req: func.HttpRequest) -> func.HttpResponse:
    """Get specific transaction details"""
    logging.info("Get transaction function triggered")

    transaction_id = req.route_params.get("id")

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
            SELECT id, order_id, amount, payment_method, status, transaction_id, created_at
            FROM transactions
            WHERE transaction_id = ? AND user_id = ?
            """,
            (transaction_id, user_id),
        )

        row = cursor.fetchone()

        if not row:
            return func.HttpResponse(
                json.dumps({"error": "Transaction not found"}),
                status_code=404,
                mimetype="application/json",
            )

        transaction = {
            "id": row[0],
            "order_id": row[1],
            "amount": float(row[2]),
            "payment_method": row[3],
            "status": row[4],
            "transaction_id": row[5],
            "created_at": row[6].isoformat() if row[6] else None,
        }

        conn.close()

        return func.HttpResponse(
            json.dumps(transaction),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Get transaction error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
