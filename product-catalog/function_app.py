import json
import logging
import os
from datetime import datetime

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


def verify_admin(session_token):
    """Verify if user is admin"""
    if not session_token:
        return False, None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT u.id, u.email
            FROM sessions s
            JOIN shopusers u ON s.user_id = u.id
            WHERE s.token = ? AND s.expires_at > ?
            """,
            (session_token, datetime.utcnow()),
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            user_id = result[0]
            email = result[1]
            is_admin = email == "admin@gmail.com"
            return is_admin, user_id
        return False, None
    except Exception as e:
        logging.error(f"Admin verification error: {str(e)}")
        return False, None


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


@app.function_name(name="GetProducts")
@app.route(route="products", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_products(req: func.HttpRequest) -> func.HttpResponse:
    """Get all products with optional filtering"""
    logging.info("Get products function triggered")

    category = req.params.get("category")
    search = req.params.get("search")
    limit = req.params.get("limit", "50")
    offset = req.params.get("offset", "0")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT id, name, description, price, stock_quantity, category, image_url, created_at FROM products WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if search:
            query += " AND (name LIKE ? OR description LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])

        query += " ORDER BY created_at DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([int(offset), int(limit)])

        cursor.execute(query, params)

        products = []
        for row in cursor.fetchall():
            products.append(
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "price": float(row[3]),
                    "stock_quantity": row[4],
                    "category": row[5],
                    "image_url": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                }
            )

        conn.close()

        return func.HttpResponse(
            json.dumps({"products": products}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Get products error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


@app.function_name(name="GetProduct")
@app.route(route="products/{id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_product(req: func.HttpRequest) -> func.HttpResponse:
    """Get single product by ID"""
    logging.info("Get product function triggered")

    product_id = req.route_params.get("id")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, name, description, price, stock_quantity, category, image_url, created_at FROM products WHERE id = ?",
            (product_id,),
        )

        row = cursor.fetchone()

        if not row:
            return func.HttpResponse(
                json.dumps({"error": "Product not found"}),
                status_code=404,
                mimetype="application/json",
            )

        product = {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "price": float(row[3]),
            "stock_quantity": row[4],
            "category": row[5],
            "image_url": row[6],
            "created_at": row[7].isoformat() if row[7] else None,
        }

        conn.close()

        return func.HttpResponse(
            json.dumps(product),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Get product error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


@app.function_name(name="CreateProduct")
@app.route(route="products", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def create_product(req: func.HttpRequest) -> func.HttpResponse:
    """Create new product (admin only)"""
    logging.info("Create product function triggered")

    # Verify admin
    session_token = req.headers.get("Authorization", "").replace("Bearer ", "")
    is_admin, user_id = verify_admin(session_token)

    if not is_admin:
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=403,
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

    name = req_body.get("name")
    description = req_body.get("description")
    price = req_body.get("price")
    stock_quantity = req_body.get("stock_quantity", 0)
    category = req_body.get("category")
    image_url = req_body.get("image_url")

    if not name or not price or not category:
        return func.HttpResponse(
            json.dumps({"error": "Name, price, and category are required"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO products (name, description, price, stock_quantity, category, image_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                description,
                price,
                stock_quantity,
                category,
                image_url,
                datetime.utcnow(),
            ),
        )
        conn.commit()

        product_id = cursor.execute("SELECT @@IDENTITY").fetchone()[0]

        conn.close()

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "product_id": product_id,
                    "name": name,
                    "price": price,
                }
            ),
            status_code=201,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Create product error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


@app.function_name(name="UpdateProduct")
@app.route(route="products/{id}", methods=["PUT"], auth_level=func.AuthLevel.ANONYMOUS)
def update_product(req: func.HttpRequest) -> func.HttpResponse:
    """Update product (admin only)"""
    logging.info("Update product function triggered")

    product_id = req.route_params.get("id")

    # Verify admin
    session_token = req.headers.get("Authorization", "").replace("Bearer ", "")
    is_admin, user_id = verify_admin(session_token)

    if not is_admin:
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=403,
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

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Build dynamic update query
        update_fields = []
        params = []

        if "name" in req_body:
            update_fields.append("name = ?")
            params.append(req_body["name"])

        if "description" in req_body:
            update_fields.append("description = ?")
            params.append(req_body["description"])

        if "price" in req_body:
            update_fields.append("price = ?")
            params.append(req_body["price"])

        if "stock_quantity" in req_body:
            update_fields.append("stock_quantity = ?")
            params.append(req_body["stock_quantity"])

        if "category" in req_body:
            update_fields.append("category = ?")
            params.append(req_body["category"])

        if "image_url" in req_body:
            update_fields.append("image_url = ?")
            params.append(req_body["image_url"])

        if not update_fields:
            return func.HttpResponse(
                json.dumps({"error": "No fields to update"}),
                status_code=400,
                mimetype="application/json",
            )

        params.append(product_id)
        query = f"UPDATE products SET {', '.join(update_fields)} WHERE id = ?"

        cursor.execute(query, params)
        conn.commit()

        if cursor.rowcount == 0:
            return func.HttpResponse(
                json.dumps({"error": "Product not found"}),
                status_code=404,
                mimetype="application/json",
            )

        conn.close()

        return func.HttpResponse(
            json.dumps({"success": True, "product_id": int(product_id)}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Update product error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


@app.function_name(name="DeleteProduct")
@app.route(
    route="products/{id}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS
)
def delete_product(req: func.HttpRequest) -> func.HttpResponse:
    """Delete product (admin only)"""
    logging.info("Delete product function triggered")

    product_id = req.route_params.get("id")

    # Verify admin
    session_token = req.headers.get("Authorization", "").replace("Bearer ", "")
    is_admin, user_id = verify_admin(session_token)

    if not is_admin:
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=403,
            mimetype="application/json",
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()

        if cursor.rowcount == 0:
            return func.HttpResponse(
                json.dumps({"error": "Product not found"}),
                status_code=404,
                mimetype="application/json",
            )

        conn.close()

        return func.HttpResponse(
            json.dumps({"success": True}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Delete product error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


# ================================================================
# SHOPPING CART ENDPOINTS
# ================================================================


@app.function_name(name="GetCart")
@app.route(route="cart", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_cart(req: func.HttpRequest) -> func.HttpResponse:
    """Get user's shopping cart"""
    logging.info("Get cart function triggered")

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
            SELECT c.id, c.product_id, c.quantity, c.added_at,
                   p.name, p.description, p.price, p.image_url, p.stock_quantity
            FROM cart_items c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
            ORDER BY c.added_at DESC
            """,
            (user_id,),
        )

        cart_items = []
        total = 0
        for row in cursor.fetchall():
            item_total = float(row[6]) * row[2]
            total += item_total
            cart_items.append(
                {
                    "id": row[0],
                    "product_id": row[1],
                    "quantity": row[2],
                    "added_at": row[3].isoformat() if row[3] else None,
                    "product": {
                        "name": row[4],
                        "description": row[5],
                        "price": float(row[6]),
                        "image_url": row[7],
                        "stock_quantity": row[8],
                    },
                    "item_total": item_total,
                }
            )

        conn.close()

        return func.HttpResponse(
            json.dumps(
                {
                    "cart_items": cart_items,
                    "total": total,
                    "item_count": len(cart_items),
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Get cart error: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


@app.function_name(name="AddToCart")
@app.route(route="cart", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def add_to_cart(req: func.HttpRequest) -> func.HttpResponse:
    """Add item to shopping cart"""
    logging.info("Add to cart function triggered")

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

        # Check if product exists and has enough stock
        cursor.execute(
            "SELECT id, name, stock_quantity FROM products WHERE id = ?",
            (product_id,),
        )
        product = cursor.fetchone()

        if not product:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Product not found"}),
                status_code=404,
                mimetype="application/json",
            )

        if product[2] < quantity:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": f"Not enough stock. Available: {product[2]}"}),
                status_code=400,
                mimetype="application/json",
            )

        # Check if item already in cart
        cursor.execute(
            "SELECT id, quantity FROM cart_items WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        existing = cursor.fetchone()

        if existing:
            # Update quantity
            new_quantity = existing[1] + quantity
            if new_quantity > product[2]:
                conn.close()
                return func.HttpResponse(
                    json.dumps({"error": f"Not enough stock. Available: {product[2]}"}),
                    status_code=400,
                    mimetype="application/json",
                )

            cursor.execute(
                "UPDATE cart_items SET quantity = ? WHERE id = ?",
                (new_quantity, existing[0]),
            )
            conn.commit()
            conn.close()

            return func.HttpResponse(
                json.dumps(
                    {
                        "success": True,
                        "message": "Cart updated",
                        "cart_item_id": existing[0],
                        "quantity": new_quantity,
                    }
                ),
                status_code=200,
                mimetype="application/json",
            )
        else:
            # Add new item
            cursor.execute(
                "INSERT INTO cart_items (user_id, product_id, quantity, added_at) VALUES (?, ?, ?, ?)",
                (user_id, product_id, quantity, datetime.utcnow()),
            )
            conn.commit()

            cart_item_id = cursor.execute("SELECT @@IDENTITY").fetchone()[0]
            conn.close()

            return func.HttpResponse(
                json.dumps(
                    {
                        "success": True,
                        "message": "Item added to cart",
                        "cart_item_id": int(cart_item_id),
                        "quantity": quantity,
                    }
                ),
                status_code=201,
                mimetype="application/json",
            )

    except Exception as e:
        logging.error(f"Add to cart error: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


@app.function_name(name="UpdateCartItem")
@app.route(route="cart/{id}", methods=["PUT"], auth_level=func.AuthLevel.ANONYMOUS)
def update_cart_item(req: func.HttpRequest) -> func.HttpResponse:
    """Update cart item quantity"""
    logging.info("Update cart item function triggered")

    cart_item_id = req.route_params.get("id")

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

    quantity = req_body.get("quantity")

    if quantity is None or quantity < 1:
        return func.HttpResponse(
            json.dumps({"error": "Quantity must be at least 1"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get cart item and verify ownership
        cursor.execute(
            "SELECT product_id FROM cart_items WHERE id = ? AND user_id = ?",
            (cart_item_id, user_id),
        )
        cart_item = cursor.fetchone()

        if not cart_item:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Cart item not found"}),
                status_code=404,
                mimetype="application/json",
            )

        product_id = cart_item[0]

        # Check stock availability
        cursor.execute(
            "SELECT stock_quantity FROM products WHERE id = ?", (product_id,)
        )
        product = cursor.fetchone()

        if not product or product[0] < quantity:
            conn.close()
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": f"Not enough stock. Available: {product[0] if product else 0}"
                    }
                ),
                status_code=400,
                mimetype="application/json",
            )

        # Update quantity
        cursor.execute(
            "UPDATE cart_items SET quantity = ? WHERE id = ?",
            (quantity, cart_item_id),
        )
        conn.commit()
        conn.close()

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "cart_item_id": int(cart_item_id),
                    "quantity": quantity,
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Update cart item error: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


@app.function_name(name="RemoveFromCart")
@app.route(route="cart/{id}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
def remove_from_cart(req: func.HttpRequest) -> func.HttpResponse:
    """Remove item from cart"""
    logging.info("Remove from cart function triggered")

    cart_item_id = req.route_params.get("id")

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
            "DELETE FROM cart_items WHERE id = ? AND user_id = ?",
            (cart_item_id, user_id),
        )
        conn.commit()

        if cursor.rowcount == 0:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Cart item not found"}),
                status_code=404,
                mimetype="application/json",
            )

        conn.close()

        return func.HttpResponse(
            json.dumps({"success": True}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Remove from cart error: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


# ================================================================
# WISHLIST ENDPOINTS
# ================================================================


@app.function_name(name="GetWishlist")
@app.route(route="wishlist", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_wishlist(req: func.HttpRequest) -> func.HttpResponse:
    """Get user's wishlist"""
    logging.info("Get wishlist function triggered")

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
            SELECT w.id, w.product_id, w.added_at,
                   p.name, p.description, p.price, p.image_url, p.stock_quantity
            FROM wishlist w
            JOIN products p ON w.product_id = p.id
            WHERE w.user_id = ?
            ORDER BY w.added_at DESC
            """,
            (user_id,),
        )

        wishlist_items = []
        for row in cursor.fetchall():
            wishlist_items.append(
                {
                    "id": row[0],
                    "product_id": row[1],
                    "added_at": row[2].isoformat() if row[2] else None,
                    "product": {
                        "name": row[3],
                        "description": row[4],
                        "price": float(row[5]),
                        "image_url": row[6],
                        "stock_quantity": row[7],
                    },
                }
            )

        conn.close()

        return func.HttpResponse(
            json.dumps(
                {"wishlist_items": wishlist_items, "item_count": len(wishlist_items)}
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Get wishlist error: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


@app.function_name(name="AddToWishlist")
@app.route(route="wishlist", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def add_to_wishlist(req: func.HttpRequest) -> func.HttpResponse:
    """Add item to wishlist"""
    logging.info("Add to wishlist function triggered")

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

        # Check if product exists
        cursor.execute("SELECT id, name FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()

        if not product:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Product not found"}),
                status_code=404,
                mimetype="application/json",
            )

        # Check if already in wishlist
        cursor.execute(
            "SELECT id FROM wishlist WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        existing = cursor.fetchone()

        if existing:
            conn.close()
            return func.HttpResponse(
                json.dumps(
                    {
                        "success": True,
                        "message": "Product already in wishlist",
                        "wishlist_item_id": existing[0],
                    }
                ),
                status_code=200,
                mimetype="application/json",
            )

        # Add to wishlist
        cursor.execute(
            "INSERT INTO wishlist (user_id, product_id, added_at) VALUES (?, ?, ?)",
            (user_id, product_id, datetime.utcnow()),
        )
        conn.commit()

        wishlist_item_id = cursor.execute("SELECT @@IDENTITY").fetchone()[0]
        conn.close()

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "message": "Item added to wishlist",
                    "wishlist_item_id": int(wishlist_item_id),
                }
            ),
            status_code=201,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Add to wishlist error: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


@app.function_name(name="RemoveFromWishlist")
@app.route(
    route="wishlist/{id}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS
)
def remove_from_wishlist(req: func.HttpRequest) -> func.HttpResponse:
    """Remove item from wishlist"""
    logging.info("Remove from wishlist function triggered")

    wishlist_item_id = req.route_params.get("id")

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
            "DELETE FROM wishlist WHERE id = ? AND user_id = ?",
            (wishlist_item_id, user_id),
        )
        conn.commit()

        if cursor.rowcount == 0:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Wishlist item not found"}),
                status_code=404,
                mimetype="application/json",
            )

        conn.close()

        return func.HttpResponse(
            json.dumps({"success": True}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Remove from wishlist error: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
