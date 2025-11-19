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
    """Create database connection using pyodbc"""
    conn_str = os.environ.get("SqlConnectionString")

    if not conn_str:
        raise ValueError("SqlConnectionString environment variable not set")

    logging.info("Attempting database connection")

    try:
        conn = pyodbc.connect(conn_str)
        logging.info("Database connection established")
        return conn
    except Exception as e:
        logging.error(f"Database connection failed: {str(e)}")
        raise


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
            JOIN shopusers u ON s.user_id = u.id
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


# ================================================================
# CHECKOUT ENDPOINT
# ================================================================


@app.function_name(name="Checkout")
@app.route(route="checkout", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def checkout(req: func.HttpRequest) -> func.HttpResponse:
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


# ================================================================
# ORDER TRACKING ENDPOINTS
# ================================================================


@app.function_name(name="GetOrders")
@app.route(route="orders", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_orders(req: func.HttpRequest) -> func.HttpResponse:
    """Get user's orders"""
    logging.info("Get orders function triggered")

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
            SELECT id, total_amount, status, shipping_address, tracking_number,
                   created_at, paid_at, shipped_at, delivered_at
            FROM orders
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        )

        orders = []
        for row in cursor.fetchall():
            orders.append(
                {
                    "id": row[0],
                    "total_amount": float(row[1]),
                    "status": row[2],
                    "shipping_address": row[3],
                    "tracking_number": row[4],
                    "created_at": row[5].isoformat() if row[5] else None,
                    "paid_at": row[6].isoformat() if row[6] else None,
                    "shipped_at": row[7].isoformat() if row[7] else None,
                    "delivered_at": row[8].isoformat() if row[8] else None,
                }
            )

        conn.close()

        return func.HttpResponse(
            json.dumps({"orders": orders, "count": len(orders)}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Get orders error: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


@app.function_name(name="GetOrder")
@app.route(route="orders/{id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_order(req: func.HttpRequest) -> func.HttpResponse:
    """Get order details with items"""
    logging.info("Get order function triggered")

    order_id = req.route_params.get("id")

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

        # Get order
        cursor.execute(
            """
            SELECT id, total_amount, status, shipping_address, tracking_number,
                   created_at, paid_at, shipped_at, delivered_at
            FROM orders
            WHERE id = ? AND user_id = ?
            """,
            (order_id, user_id),
        )
        order_row = cursor.fetchone()

        if not order_row:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Order not found"}),
                status_code=404,
                mimetype="application/json",
            )

        # Get order items
        cursor.execute(
            """
            SELECT oi.id, oi.product_id, oi.quantity, oi.price_at_purchase,
                   p.name, p.description, p.image_url
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
            """,
            (order_id,),
        )

        items = []
        for item_row in cursor.fetchall():
            items.append(
                {
                    "id": item_row[0],
                    "product_id": item_row[1],
                    "quantity": item_row[2],
                    "price_at_purchase": float(item_row[3]),
                    "product": {
                        "name": item_row[4],
                        "description": item_row[5],
                        "image_url": item_row[6],
                    },
                    "item_total": float(item_row[3]) * item_row[2],
                }
            )

        conn.close()

        order = {
            "id": order_row[0],
            "total_amount": float(order_row[1]),
            "status": order_row[2],
            "shipping_address": order_row[3],
            "tracking_number": order_row[4],
            "created_at": order_row[5].isoformat() if order_row[5] else None,
            "paid_at": order_row[6].isoformat() if order_row[6] else None,
            "shipped_at": order_row[7].isoformat() if order_row[7] else None,
            "delivered_at": order_row[8].isoformat() if order_row[8] else None,
            "items": items,
        }

        return func.HttpResponse(
            json.dumps(order), status_code=200, mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Get order error: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


@app.function_name(name="UpdateOrderStatus")
@app.route(
    route="orders/{id}/status", methods=["PUT"], auth_level=func.AuthLevel.ANONYMOUS
)
def update_order_status(req: func.HttpRequest) -> func.HttpResponse:
    """Update order status (admin only)"""
    logging.info("Update order status function triggered")

    order_id = req.route_params.get("id")

    # Verify admin
    session_token = req.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = verify_session(session_token)

    if not user_id:
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=401,
            mimetype="application/json",
        )

    # Check if admin
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT email FROM shopusers WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if not user or user[0] != "admin@gmail.com":
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Forbidden - Admin access required"}),
                status_code=403,
                mimetype="application/json",
            )

        # Get request body
        try:
            req_body = req.get_json()
        except ValueError:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON"}),
                status_code=400,
                mimetype="application/json",
            )

        status = req_body.get("status")
        tracking_number = req_body.get("tracking_number")

        valid_statuses = [
            "pending",
            "paid",
            "processing",
            "shipped",
            "delivered",
            "cancelled",
        ]
        if status and status not in valid_statuses:
            conn.close()
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": f"Invalid status. Valid statuses: {', '.join(valid_statuses)}"
                    }
                ),
                status_code=400,
                mimetype="application/json",
            )

        # Build update query
        updates = []
        params = []

        if status:
            updates.append("status = ?")
            params.append(status)

            # Set timestamps based on status
            if status == "shipped":
                updates.append("shipped_at = ?")
                params.append(datetime.utcnow())
            elif status == "delivered":
                updates.append("delivered_at = ?")
                params.append(datetime.utcnow())

        if tracking_number:
            updates.append("tracking_number = ?")
            params.append(tracking_number)

        if not updates:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "No fields to update"}),
                status_code=400,
                mimetype="application/json",
            )

        params.append(order_id)
        query = f"UPDATE orders SET {', '.join(updates)} WHERE id = ?"

        cursor.execute(query, params)
        conn.commit()

        if cursor.rowcount == 0:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Order not found"}),
                status_code=404,
                mimetype="application/json",
            )

        conn.close()

        logging.info(f"Order {order_id} status updated to {status}")
        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "order_id": int(order_id),
                    "status": status,
                    "tracking_number": tracking_number,
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Update order status error: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


@app.function_name(name="TrackOrder")
@app.route(
    route="orders/{id}/track", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS
)
def track_order(req: func.HttpRequest) -> func.HttpResponse:
    """Track order delivery status"""
    logging.info("Track order function triggered")

    order_id = req.route_params.get("id")

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
            SELECT status, tracking_number, created_at, paid_at, shipped_at, delivered_at
            FROM orders
            WHERE id = ? AND user_id = ?
            """,
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

        conn.close()

        tracking_info = {
            "order_id": int(order_id),
            "status": order[0],
            "tracking_number": order[1],
            "timeline": {
                "ordered": order[2].isoformat() if order[2] else None,
                "paid": order[3].isoformat() if order[3] else None,
                "shipped": order[4].isoformat() if order[4] else None,
                "delivered": order[5].isoformat() if order[5] else None,
            },
        }

        return func.HttpResponse(
            json.dumps(tracking_info),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Track order error: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
