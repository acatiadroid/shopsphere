import base64
import os
from functools import wraps

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
USER_AUTH_URL = "https://user-auth-feh2gugugngnbxbp.norwayeast-01.azurewebsites.net/api"
PRODUCT_CATALOG_URL = (
    "https://product-catalog-ffcjf2heceech3f6.norwayeast-01.azurewebsites.net/api"
)
PAYMENT_URL = "https://payment-bxehasc6bshbdpd2.norwayeast-01.azurewebsites.net/api"

CDN_BASE_URL = "https://shopsphere.blob.core.windows.net/cdn/"


def get_auth_headers():
    """Get authorization headers with session token"""
    if "session_token" in session:
        return {"Authorization": f"Bearer {session['session_token']}"}
    return {}


def login_required(f):
    """Decorator to require login"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "session_token" not in session:
            flash("Please login to access this page", "warning")
            return redirect(url_for("login"))

        # Verify session is still valid
        try:
            response = requests.post(
                f"{USER_AUTH_URL}/auth/verify",
                json={"session_token": session["session_token"]},
                timeout=5,
            )
            if not response.ok:
                session.clear()
                flash("Session expired. Please login again.", "warning")
                return redirect(url_for("login"))
        except Exception:
            pass  # Continue if verification fails temporarily

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """Decorator to require admin access"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "session_token" not in session:
            flash("Please login to access this page", "warning")
            return redirect(url_for("login"))

        # Check if user is admin (admin@gmail.com)
        user = session.get("user", {})
        if user.get("email") != "admin@gmail.com":
            flash("Admin access required", "danger")
            return redirect(url_for("index"))

        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def index():
    """Homepage with product listings"""
    try:
        # Get products from Azure Function
        response = requests.get(f"{PRODUCT_CATALOG_URL}/products", timeout=10)
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
        response = requests.get(
            f"{PRODUCT_CATALOG_URL}/products/{product_id}", timeout=10
        )

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
                f"{USER_AUTH_URL}/auth/signup",
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
                user_data = data.get("user", {})
                session["user"] = {
                    "id": user_data.get("id"),
                    "email": user_data.get("email"),
                    "name": user_data.get("name"),
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
                f"{USER_AUTH_URL}/auth/login",
                json={"email": email, "password": password},
                timeout=10,
            )

            if response.ok:
                data = response.json()
                session["session_token"] = data["session_token"]
                user_data = data.get("user", {})
                session["user"] = {
                    "id": user_data.get("id"),
                    "email": user_data.get("email"),
                    "name": user_data.get("name"),
                }
                flash(f"Welcome back, {user_data.get('name')}!", "success")
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
                f"{USER_AUTH_URL}/auth/logout",
                json={"session_token": session["session_token"]},
                timeout=10,
            )
    except Exception:
        pass

    session.clear()
    flash("You have been logged out", "info")
    return redirect(url_for("index"))


@app.route("/cart")
@login_required
def cart():
    """Shopping cart page"""
    try:
        # Get cart items from Azure Function
        response = requests.get(
            f"{PRODUCT_CATALOG_URL}/cart",
            headers=get_auth_headers(),
            timeout=10,
        )

        if response.ok:
            data = response.json()
            cart_items = data.get("cart_items", [])
            # Calculate total from item_total field or compute it
            total = data.get(
                "total", sum(item.get("item_total", 0) for item in cart_items)
            )

            # Transform data to match template expectations
            for item in cart_items:
                product_data = item.get("product", {})
                item["name"] = product_data.get("name")
                item["price"] = product_data.get("price")
                item["image_url"] = product_data.get("image_url")
                item["stock_quantity"] = product_data.get("stock_quantity")
                item["subtotal"] = item.get("item_total", 0)
        else:
            cart_items = []
            total = 0

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

        response = requests.post(
            f"{PRODUCT_CATALOG_URL}/cart",
            json={"product_id": product_id, "quantity": quantity},
            headers=get_auth_headers(),
            timeout=10,
        )

        if response.ok:
            flash("Product added to cart", "success")
            return redirect(url_for("cart"))
        else:
            error = response.json().get("error", "Failed to add to cart")
            flash(error, "danger")
            return redirect(url_for("product_detail", product_id=product_id))

    except Exception as e:
        flash(f"Error adding to cart: {str(e)}", "danger")
        return redirect(url_for("index"))


@app.route("/cart/update/<int:cart_item_id>", methods=["POST"])
@login_required
def update_cart(cart_item_id):
    """Update cart item quantity"""
    try:
        quantity = int(request.form.get("quantity", 1))

        response = requests.put(
            f"{PRODUCT_CATALOG_URL}/cart/{cart_item_id}",
            json={"quantity": quantity},
            headers=get_auth_headers(),
            timeout=10,
        )

        if response.ok:
            flash("Cart updated", "success")
        else:
            error = response.json().get("error", "Failed to update cart")
            flash(error, "danger")

    except Exception as e:
        flash(f"Error updating cart: {str(e)}", "danger")

    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:cart_item_id>", methods=["POST"])
@login_required
def remove_from_cart(cart_item_id):
    """Remove item from cart"""
    try:
        response = requests.delete(
            f"{PRODUCT_CATALOG_URL}/cart/{cart_item_id}",
            headers=get_auth_headers(),
            timeout=10,
        )

        if response.ok:
            flash("Item removed from cart", "success")
        else:
            error = response.json().get("error", "Failed to remove item")
            flash(error, "danger")

    except Exception as e:
        flash(f"Error removing item: {str(e)}", "danger")

    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    """Checkout page"""
    if request.method == "POST":
        try:
            # Check if using a saved payment method or a new one
            payment_method_id = request.form.get("payment_method_id")
            payment_method = request.form.get("payment_method", "credit_card")

            # If using a saved payment method, fetch its details
            if payment_method_id and payment_method_id != "new":
                try:
                    pm_response = requests.get(
                        f"{USER_AUTH_URL}/payment-methods",
                        headers=get_auth_headers(),
                        timeout=10,
                    )
                    if pm_response.ok:
                        methods = pm_response.json().get("payment_methods", [])
                        selected_method = next(
                            (m for m in methods if str(m["id"]) == payment_method_id),
                            None,
                        )
                        if selected_method:
                            payment_method = selected_method["payment_type"]
                except Exception:
                    pass  # Fall back to default payment_method if lookup fails

            # Collect shipping address fields
            shipping_name = request.form.get("shipping_name", "").strip()
            shipping_address_line1 = request.form.get(
                "shipping_address_line1", ""
            ).strip()
            shipping_address_line2 = request.form.get(
                "shipping_address_line2", ""
            ).strip()
            shipping_city = request.form.get("shipping_city", "").strip()
            shipping_state = request.form.get("shipping_state", "").strip()
            shipping_postal_code = request.form.get("shipping_postal_code", "").strip()
            shipping_country = request.form.get("shipping_country", "").strip()
            shipping_phone = request.form.get("shipping_phone", "").strip()

            # Validate required fields
            if not all(
                [
                    shipping_name,
                    shipping_address_line1,
                    shipping_city,
                    shipping_state,
                    shipping_postal_code,
                    shipping_country,
                ]
            ):
                flash("Please fill in all required shipping address fields", "danger")
                return redirect(url_for("checkout"))

            # Format shipping address
            shipping_address_parts = [
                shipping_name,
                shipping_address_line1,
            ]
            if shipping_address_line2:
                shipping_address_parts.append(shipping_address_line2)
            shipping_address_parts.extend(
                [
                    f"{shipping_city}, {shipping_state} {shipping_postal_code}",
                    shipping_country,
                ]
            )
            if shipping_phone:
                shipping_address_parts.append(f"Phone: {shipping_phone}")

            shipping_address = "\n".join(shipping_address_parts)

            # Call checkout Azure Function
            response = requests.post(
                f"{PAYMENT_URL}/checkout",
                json={
                    "payment_method": payment_method,
                    "shipping_address": shipping_address,
                },
                headers=get_auth_headers(),
                timeout=15,
            )

            if response.ok:
                data = response.json()

                if data.get("success"):
                    order_id = data.get("order_id")
                    # Checkout doesn't return transaction_id, just order_id
                    flash(
                        f"Order placed successfully! Order ID: {order_id}",
                        "success",
                    )
                    return redirect(url_for("order_detail", order_id=order_id))
                else:
                    error = data.get("error", "Checkout failed")
                    flash(error, "danger")
            else:
                error = response.json().get("error", "Checkout failed")
                flash(error, "danger")

        except Exception as e:
            flash(f"Error during checkout: {str(e)}", "danger")

        return redirect(url_for("checkout"))

    # GET request - show checkout form
    try:
        # Get cart items for display
        response = requests.get(
            f"{PRODUCT_CATALOG_URL}/cart",
            headers=get_auth_headers(),
            timeout=10,
        )

        if response.ok:
            data = response.json()
            cart_items = data.get("cart_items", [])
            total = data.get(
                "total", sum(item.get("item_total", 0) for item in cart_items)
            )

            # Transform data to match template expectations
            for item in cart_items:
                product_data = item.get("product", {})
                item["name"] = product_data.get("name")
                item["price"] = product_data.get("price")
                item["image_url"] = product_data.get("image_url")
                item["stock_quantity"] = product_data.get("stock_quantity")
                item["subtotal"] = item.get("item_total", 0)
        else:
            cart_items = []
            total = 0

        if not cart_items:
            flash("Your cart is empty", "warning")
            return redirect(url_for("cart"))

        # Get saved payment methods
        payment_methods = []
        try:
            pm_response = requests.get(
                f"{USER_AUTH_URL}/payment-methods",
                headers=get_auth_headers(),
                timeout=10,
            )
            if pm_response.ok:
                pm_data = pm_response.json()
                payment_methods = pm_data.get("payment_methods", [])
        except Exception:
            pass  # Continue without payment methods if request fails

        return render_template(
            "checkout.html",
            cart_items=cart_items,
            total=total,
            payment_methods=payment_methods,
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
        response = requests.get(
            f"{PAYMENT_URL}/orders",
            headers=get_auth_headers(),
            timeout=10,
        )

        if response.ok:
            data = response.json()
            orders_list = data.get("orders", [])
        else:
            orders_list = []

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
        # Get order details
        response = requests.get(
            f"{PAYMENT_URL}/orders/{order_id}",
            headers=get_auth_headers(),
            timeout=10,
        )

        if response.status_code == 404:
            flash("Order not found", "warning")
            return redirect(url_for("orders"))

        if not response.ok:
            flash("Error loading order", "danger")
            return redirect(url_for("orders"))

        # GetOrder returns flat structure with items included
        order_data = response.json()
        items = order_data.pop("items", [])
        order = order_data

        # Transform items to match template expectations
        for item in items:
            product_data = item.get("product", {})
            item["name"] = product_data.get("name")
            item["image_url"] = product_data.get("image_url")
            item["price"] = item.get("price_at_purchase", 0)
            item["subtotal"] = item.get("item_total", 0)

        # Get tracking information
        try:
            tracking_response = requests.get(
                f"{PAYMENT_URL}/orders/{order_id}/track",
                headers=get_auth_headers(),
                timeout=10,
            )

            if tracking_response.ok:
                tracking_data = tracking_response.json()
                order["tracking"] = tracking_data.get("tracking", {})
        except Exception:
            pass  # Tracking is optional

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
        response = requests.get(
            f"{PRODUCT_CATALOG_URL}/wishlist",
            headers=get_auth_headers(),
            timeout=10,
        )

        if response.ok:
            data = response.json()
            wishlist_items = data.get("wishlist_items", [])

            # Transform data to match template expectations
            for item in wishlist_items:
                product_data = item.get("product", {})
                item["name"] = product_data.get("name")
                item["price"] = product_data.get("price")
                item["image_url"] = product_data.get("image_url")
                item["stock_quantity"] = product_data.get("stock_quantity")
        else:
            wishlist_items = []

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
        response = requests.post(
            f"{PRODUCT_CATALOG_URL}/wishlist",
            json={"product_id": product_id},
            headers=get_auth_headers(),
            timeout=10,
        )

        if response.ok:
            flash("Product added to wishlist", "success")
        else:
            error = response.json().get("error", "Failed to add to wishlist")
            if "already" in error.lower():
                flash("Product already in wishlist", "info")
            else:
                flash(error, "danger")

    except Exception as e:
        flash(f"Error adding to wishlist: {str(e)}", "danger")

    return redirect(request.referrer or url_for("index"))


@app.route("/wishlist/remove/<int:wishlist_id>", methods=["POST"])
@login_required
def remove_from_wishlist(wishlist_id):
    """Remove product from wishlist"""
    try:
        response = requests.delete(
            f"{PRODUCT_CATALOG_URL}/wishlist/{wishlist_id}",
            headers=get_auth_headers(),
            timeout=10,
        )

        if response.ok:
            flash("Product removed from wishlist", "success")
        else:
            error = response.json().get("error", "Failed to remove from wishlist")
            flash(error, "danger")

    except Exception as e:
        flash(f"Error removing from wishlist: {str(e)}", "danger")

    return redirect(url_for("wishlist"))


@app.route("/admin/products", methods=["GET", "POST"])
@admin_required
def admin_products():
    """Admin page to manage products"""
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        price = request.form.get("price")
        stock_quantity = request.form.get("stock_quantity", 0)
        category = request.form.get("category")
        image_url = request.form.get("image_url")

        # Handle image upload if file is provided
        image_data = None
        if "product_image" in request.files:
            file = request.files["product_image"]
            if file and file.filename != "":
                try:
                    # Read file and convert to base64
                    file_bytes = file.read()
                    image_data = base64.b64encode(file_bytes).decode("utf-8")

                    # Add data URL prefix with content type
                    content_type = file.content_type or "image/jpeg"
                    image_data = f"data:{content_type};base64,{image_data}"
                except Exception as e:
                    flash(f"Failed to process image: {str(e)}", "warning")

        try:
            # Prepare product data
            product_data = {
                "name": name,
                "description": description,
                "price": float(price),
                "stock_quantity": int(stock_quantity),
                "category": category,
            }

            # Add image data or URL
            if image_data:
                product_data["image_data"] = image_data
            elif image_url:
                product_data["image_url"] = image_url
            response = requests.post(
                f"{PRODUCT_CATALOG_URL}/products",
                json=product_data,
                headers=get_auth_headers(),
                timeout=30,  # Increased timeout for image upload
            )

            if response.ok:
                data = response.json()
                success_msg = (
                    f"Product '{name}' added successfully! ID: {data.get('product_id')}"
                )
                if image_data:
                    success_msg += " (with image)"
                flash(success_msg, "success")
                return redirect(url_for("admin_products"))
            else:
                error = response.json().get("error", "Failed to add product")
                flash(error, "danger")
        except Exception as e:
            flash(f"Error adding product: {str(e)}", "danger")

    # GET request - show form and product list
    try:
        response = requests.get(f"{PRODUCT_CATALOG_URL}/products", timeout=10)
        products = response.json().get("products", []) if response.ok else []
    except Exception as e:
        flash(f"Error loading products: {str(e)}", "danger")
        products = []

    return render_template(
        "admin_products.html", products=products, user=session.get("user")
    )


@app.route("/transactions")
@login_required
def transactions():
    """User's transaction history"""
    try:
        response = requests.get(
            f"{PAYMENT_URL}/payment/transactions",
            headers=get_auth_headers(),
            timeout=10,
        )

        if response.ok:
            data = response.json()
            transactions_list = data.get("transactions", [])
        else:
            transactions_list = []

        return render_template(
            "transactions.html",
            transactions=transactions_list,
            user=session.get("user"),
        )
    except Exception as e:
        flash(f"Error loading transactions: {str(e)}", "danger")
        return render_template(
            "transactions.html", transactions=[], user=session.get("user")
        )


@app.route("/payment-methods")
@login_required
def payment_methods():
    """Manage payment methods"""
    try:
        # Get user's payment methods
        response = requests.get(
            f"{USER_AUTH_URL}/payment-methods",
            headers=get_auth_headers(),
            timeout=10,
        )

        if response.ok:
            data = response.json()
            methods = data.get("payment_methods", [])
        else:
            methods = []

        return render_template(
            "payment_methods.html",
            payment_methods=methods,
            user=session.get("user"),
        )
    except Exception as e:
        flash(f"Error loading payment methods: {str(e)}", "danger")
        return render_template(
            "payment_methods.html", payment_methods=[], user=session.get("user")
        )


@app.route("/payment-methods/add", methods=["POST"])
@login_required
def add_payment_method():
    """Add a new payment method"""
    try:
        payment_type = request.form.get("payment_type")
        card_last_four = request.form.get("card_last_four", "").strip()
        card_brand = request.form.get("card_brand", "").strip()
        cardholder_name = request.form.get("cardholder_name", "").strip()
        expiry_month = request.form.get("expiry_month", "").strip()
        expiry_year = request.form.get("expiry_year", "").strip()
        is_default = request.form.get("is_default") == "on"

        # Build payload
        payload = {
            "payment_type": payment_type,
            "is_default": is_default,
        }

        # Add card details if it's a card payment type
        if payment_type in ["credit_card", "debit_card"]:
            payload["card_last_four"] = card_last_four
            payload["card_brand"] = card_brand
            payload["cardholder_name"] = cardholder_name
            if expiry_month:
                payload["expiry_month"] = int(expiry_month)
            if expiry_year:
                payload["expiry_year"] = int(expiry_year)

        response = requests.post(
            f"{USER_AUTH_URL}/payment-methods",
            json=payload,
            headers=get_auth_headers(),
            timeout=10,
        )

        if response.ok:
            flash("Payment method added successfully", "success")
        else:
            error = response.json().get("error", "Failed to add payment method")
            flash(error, "danger")

    except Exception as e:
        flash(f"Error adding payment method: {str(e)}", "danger")

    return redirect(url_for("payment_methods"))


@app.route("/payment-methods/<int:method_id>/delete", methods=["POST"])
@login_required
def delete_payment_method(method_id):
    """Delete a payment method"""
    try:
        response = requests.delete(
            f"{USER_AUTH_URL}/payment-methods/{method_id}",
            headers=get_auth_headers(),
            timeout=10,
        )

        if response.ok:
            flash("Payment method deleted successfully", "success")
        else:
            error = response.json().get("error", "Failed to delete payment method")
            flash(error, "danger")

    except Exception as e:
        flash(f"Error deleting payment method: {str(e)}", "danger")

    return redirect(url_for("payment_methods"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
