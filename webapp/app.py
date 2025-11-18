import os
from datetime import datetime
from functools import wraps

import pytds
import requests
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# Azure Function URLs
USER_AUTH_URL = (
    "https://user-auth-feh2gugugngnbxbp.norwayeast-01.azurewebsites.net/api/auth"
)
PRODUCT_CATALOG_URL = "https://product-catalog-ffcjf2heceech3f6.norwayeast-01.azurewebsites.net/api/products"
PAYMENT_URL = (
    "https://payment-bxehasc6bshbdpd2.norwayeast-01.azurewebsites.net/api/payment"
)

# Database connection settings
DB_SERVER = os.environ.get("DB_SERVER", "luke-shopsphere.database.windows.net")
DB_NAME = os.environ.get("DB_NAME", "luke-database")
DB_USER = os.environ.get("DB_USER", "myadmin")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "Abcdefgh0!")
CDN_BASE_URL = "https://shopsphere.blob.core.windows.net/cdn/"


def get_db_connection():
    """Create database connection"""
    return pytds.connect(
        dsn=DB_SERVER,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=1433,
        autocommit=False,
    )


def login_required(f):
    """Decorator to require login"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "session_token" not in session:
            flash("Please login to access this page", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def index():
    """Homepage with product listings"""
    try:
        # Get products from Azure Function
        response = requests.get(PRODUCT_CATALOG_URL, timeout=10)
        products = response.json().get("products", []) if response.ok else []

        # Get categories
        categories = list(set(p.get("category", "Other") for p in products))
        categories.sort()

        return render_template(
            "index.html",
            products=products,
            categories=categories,
            user=session.get("user"),
        )
    except Exception as e:
        flash(f"Error loading products: {str(e)}", "danger")
        return render_template("index.html", products=[], categories=[], user=None)


@app.route("/products/<int:product_id>")
def product_detail(product_id):
    """Product detail page"""
    try:
        response = requests.get(f"{PRODUCT_CATALOG_URL}/{product_id}", timeout=10)

        if response.status_code == 404:
            flash("Product not found", "warning")
            return redirect(url_for("index"))

        product = response.json() if response.ok else None

        return render_template(
            "product_detail.html", product=product, user=session.get("user")
        )
    except Exception as e:
        flash(f"Error loading product: {str(e)}", "danger")
        return redirect(url_for("index"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """User signup"""
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            response = requests.post(
                f"{USER_AUTH_URL}/signup",
                json={"name": name, "email": email, "password": password},
                timeout=10,
            )

            if response.ok:
                try:
                    data = response.json()
                except ValueError:
                    flash(
                        f"Invalid response from server: {response.text[:200]}", "danger"
                    )
                    return render_template("signup.html")

                session["session_token"] = data["session_token"]
                session["user"] = {
                    "id": data["user_id"],
                    "email": data["email"],
                    "name": data["name"],
                }
                flash(f"Welcome, {name}!", "success")
                return redirect(url_for("index"))
            else:
                try:
                    error = response.json().get("error", "Signup failed")
                except ValueError:
                    error = f"Signup failed: {response.text[:200]}"
                flash(error, "danger")
        except requests.exceptions.RequestException as e:
            flash(f"Connection error: {str(e)}", "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login"""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            response = requests.post(
                f"{USER_AUTH_URL}/login",
                json={"email": email, "password": password},
                timeout=10,
            )

            if response.ok:
                data = response.json()
                session["session_token"] = data["session_token"]
                session["user"] = {
                    "id": data["user_id"],
                    "email": data["email"],
                    "name": data["name"],
                }
                flash(f"Welcome back, {data['name']}!", "success")
                return redirect(url_for("index"))
            else:
                error = response.json().get("error", "Login failed")
                flash(error, "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """User logout"""
    try:
        if "session_token" in session:
            requests.post(
                f"{USER_AUTH_URL}/logout",
                json={"session_token": session["session_token"]},
                timeout=10,
            )
    except:
        pass

    session.clear()
    flash("You have been logged out", "info")
    return redirect(url_for("index"))


@app.route("/cart")
@login_required
def cart():
    """Shopping cart page"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get cart items
        cursor.execute(
            """
            SELECT c.id, c.product_id, c.quantity, p.name, p.price, p.image_url, p.stock_quantity
            FROM cart_items c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
            """,
            (session["user"]["id"],),
        )

        cart_items = []
        total = 0

        for row in cursor.fetchall():
            item = {
                "id": row[0],
                "product_id": row[1],
                "quantity": row[2],
                "name": row[3],
                "price": float(row[4]),
                "image_url": row[5],
                "stock_quantity": row[6],
                "subtotal": float(row[4]) * row[2],
            }
            cart_items.append(item)
            total += item["subtotal"]

        conn.close()

        return render_template(
            "cart.html", cart_items=cart_items, total=total, user=session.get("user")
        )
    except Exception as e:
        flash(f"Error loading cart: {str(e)}", "danger")
        return render_template(
            "cart.html", cart_items=[], total=0, user=session.get("user")
        )


@app.route("/cart/add/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    """Add product to cart"""
    try:
        quantity = int(request.form.get("quantity", 1))

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if product exists and has stock
        cursor.execute(
            "SELECT stock_quantity FROM products WHERE id = ?", (product_id,)
        )
        product = cursor.fetchone()

        if not product:
            flash("Product not found", "danger")
            return redirect(url_for("index"))

        if product[0] < quantity:
            flash("Not enough stock available", "warning")
            return redirect(url_for("product_detail", product_id=product_id))

        # Check if item already in cart
        cursor.execute(
            "SELECT id, quantity FROM cart_items WHERE user_id = ? AND product_id = ?",
            (session["user"]["id"], product_id),
        )
        existing = cursor.fetchone()

        if existing:
            # Update quantity
            new_quantity = existing[1] + quantity
            cursor.execute(
                "UPDATE cart_items SET quantity = ? WHERE id = ?",
                (new_quantity, existing[0]),
            )
        else:
            # Add new item
            cursor.execute(
                "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)",
                (session["user"]["id"], product_id, quantity),
            )

        conn.commit()
        conn.close()

        flash("Product added to cart", "success")
        return redirect(url_for("cart"))
    except Exception as e:
        flash(f"Error adding to cart: {str(e)}", "danger")
        return redirect(url_for("index"))


@app.route("/cart/update/<int:cart_item_id>", methods=["POST"])
@login_required
def update_cart(cart_item_id):
    """Update cart item quantity"""
    try:
        quantity = int(request.form.get("quantity", 1))

        conn = get_db_connection()
        cursor = conn.cursor()

        if quantity <= 0:
            cursor.execute(
                "DELETE FROM cart_items WHERE id = ? AND user_id = ?",
                (cart_item_id, session["user"]["id"]),
            )
        else:
            cursor.execute(
                "UPDATE cart_items SET quantity = ? WHERE id = ? AND user_id = ?",
                (quantity, cart_item_id, session["user"]["id"]),
            )

        conn.commit()
        conn.close()

        flash("Cart updated", "success")
    except Exception as e:
        flash(f"Error updating cart: {str(e)}", "danger")

    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:cart_item_id>", methods=["POST"])
@login_required
def remove_from_cart(cart_item_id):
    """Remove item from cart"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM cart_items WHERE id = ? AND user_id = ?",
            (cart_item_id, session["user"]["id"]),
        )

        conn.commit()
        conn.close()

        flash("Item removed from cart", "success")
    except Exception as e:
        flash(f"Error removing item: {str(e)}", "danger")

    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    """Checkout page"""
    if request.method == "POST":
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Get cart items
            cursor.execute(
                """
                SELECT c.product_id, c.quantity, p.price, p.stock_quantity
                FROM cart_items c
                JOIN products p ON c.product_id = p.id
                WHERE c.user_id = ?
                """,
                (session["user"]["id"],),
            )

            cart_items = cursor.fetchall()

            if not cart_items:
                flash("Your cart is empty", "warning")
                return redirect(url_for("cart"))

            # Calculate total and validate stock
            total = 0
            for item in cart_items:
                product_id, quantity, price, stock = item
                if stock < quantity:
                    flash("Some items are out of stock", "danger")
                    return redirect(url_for("cart"))
                total += float(price) * quantity

            # Create order
            cursor.execute(
                "INSERT INTO orders (user_id, total_amount, status, created_at) VALUES (?, ?, ?, ?)",
                (session["user"]["id"], total, "pending", datetime.utcnow()),
            )
            conn.commit()

            order_id = cursor.execute("SELECT @@IDENTITY").fetchone()[0]

            # Create order items
            for item in cart_items:
                product_id, quantity, price, _ = item
                cursor.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                    (order_id, product_id, quantity, price),
                )

            conn.commit()

            # Process payment
            payment_method = request.form.get("payment_method", "credit_card")

            headers = {"Authorization": f"Bearer {session['session_token']}"}
            response = requests.post(
                f"{PAYMENT_URL}/process",
                json={
                    "order_id": order_id,
                    "amount": total,
                    "payment_method": payment_method,
                },
                headers=headers,
                timeout=10,
            )

            if response.ok:
                data = response.json()

                if data.get("success"):
                    # Update stock quantities
                    for item in cart_items:
                        product_id, quantity, _, _ = item
                        cursor.execute(
                            "UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?",
                            (quantity, product_id),
                        )

                    # Clear cart
                    cursor.execute(
                        "DELETE FROM cart_items WHERE user_id = ?",
                        (session["user"]["id"],),
                    )

                    conn.commit()
                    conn.close()

                    flash(
                        f"Order placed successfully! Transaction ID: {data['transaction_id']}",
                        "success",
                    )
                    return redirect(url_for("order_detail", order_id=order_id))
                else:
                    flash("Payment failed. Please try again.", "danger")
            else:
                flash("Payment processing error", "danger")

            conn.close()

        except Exception as e:
            flash(f"Error during checkout: {str(e)}", "danger")

    # GET request - show checkout form
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT c.id, c.product_id, c.quantity, p.name, p.price
            FROM cart_items c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
            """,
            (session["user"]["id"],),
        )

        cart_items = []
        total = 0

        for row in cursor.fetchall():
            item = {
                "id": row[0],
                "product_id": row[1],
                "quantity": row[2],
                "name": row[3],
                "price": float(row[4]),
                "subtotal": float(row[4]) * row[2],
            }
            cart_items.append(item)
            total += item["subtotal"]

        conn.close()

        return render_template(
            "checkout.html",
            cart_items=cart_items,
            total=total,
            user=session.get("user"),
        )
    except Exception as e:
        flash(f"Error loading checkout: {str(e)}", "danger")
        return redirect(url_for("cart"))


@app.route("/orders")
@login_required
def orders():
    """User's order history"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, total_amount, status, created_at, paid_at
            FROM orders
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (session["user"]["id"],),
        )

        orders_list = []
        for row in cursor.fetchall():
            orders_list.append(
                {
                    "id": row[0],
                    "total_amount": float(row[1]),
                    "status": row[2],
                    "created_at": row[3],
                    "paid_at": row[4],
                }
            )

        conn.close()

        return render_template(
            "orders.html", orders=orders_list, user=session.get("user")
        )
    except Exception as e:
        flash(f"Error loading orders: {str(e)}", "danger")
        return render_template("orders.html", orders=[], user=session.get("user"))


@app.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    """Order detail page with tracking"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get order
        cursor.execute(
            """
            SELECT id, total_amount, status, created_at, paid_at
            FROM orders
            WHERE id = ? AND user_id = ?
            """,
            (order_id, session["user"]["id"]),
        )

        order_row = cursor.fetchone()

        if not order_row:
            flash("Order not found", "warning")
            return redirect(url_for("orders"))

        order = {
            "id": order_row[0],
            "total_amount": float(order_row[1]),
            "status": order_row[2],
            "created_at": order_row[3],
            "paid_at": order_row[4],
        }

        # Get order items
        cursor.execute(
            """
            SELECT oi.quantity, oi.price, p.name, p.image_url
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
            """,
            (order_id,),
        )

        items = []
        for row in cursor.fetchall():
            items.append(
                {
                    "quantity": row[0],
                    "price": float(row[1]),
                    "name": row[2],
                    "image_url": row[3],
                    "subtotal": float(row[1]) * row[0],
                }
            )

        conn.close()

        return render_template(
            "order_detail.html", order=order, items=items, user=session.get("user")
        )
    except Exception as e:
        flash(f"Error loading order: {str(e)}", "danger")
        return redirect(url_for("orders"))


@app.route("/wishlist")
@login_required
def wishlist():
    """User's wishlist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT w.id, w.product_id, p.name, p.price, p.image_url, p.stock_quantity
            FROM wishlist w
            JOIN products p ON w.product_id = p.id
            WHERE w.user_id = ?
            ORDER BY w.created_at DESC
            """,
            (session["user"]["id"],),
        )

        wishlist_items = []
        for row in cursor.fetchall():
            wishlist_items.append(
                {
                    "id": row[0],
                    "product_id": row[1],
                    "name": row[2],
                    "price": float(row[3]),
                    "image_url": row[4],
                    "stock_quantity": row[5],
                }
            )

        conn.close()

        return render_template(
            "wishlist.html", wishlist_items=wishlist_items, user=session.get("user")
        )
    except Exception as e:
        flash(f"Error loading wishlist: {str(e)}", "danger")
        return render_template(
            "wishlist.html", wishlist_items=[], user=session.get("user")
        )


@app.route("/wishlist/add/<int:product_id>", methods=["POST"])
@login_required
def add_to_wishlist(product_id):
    """Add product to wishlist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if already in wishlist
        cursor.execute(
            "SELECT id FROM wishlist WHERE user_id = ? AND product_id = ?",
            (session["user"]["id"], product_id),
        )

        if cursor.fetchone():
            flash("Product already in wishlist", "info")
        else:
            cursor.execute(
                "INSERT INTO wishlist (user_id, product_id, created_at) VALUES (?, ?, ?)",
                (session["user"]["id"], product_id, datetime.utcnow()),
            )
            conn.commit()
            flash("Product added to wishlist", "success")

        conn.close()
    except Exception as e:
        flash(f"Error adding to wishlist: {str(e)}", "danger")

    return redirect(request.referrer or url_for("index"))


@app.route("/wishlist/remove/<int:wishlist_id>", methods=["POST"])
@login_required
def remove_from_wishlist(wishlist_id):
    """Remove product from wishlist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM wishlist WHERE id = ? AND user_id = ?",
            (wishlist_id, session["user"]["id"]),
        )

        conn.commit()
        conn.close()

        flash("Product removed from wishlist", "success")
    except Exception as e:
        flash(f"Error removing from wishlist: {str(e)}", "danger")

    return redirect(url_for("wishlist"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
