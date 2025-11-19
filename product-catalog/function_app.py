import json
import logging
import os
from datetime import datetime

import azure.functions as func
import pyodbc

app = func.FunctionApp()


def get_db_connection():
    """Create database connection"""
    conn_str = os.environ.get("SqlConnectionString")
    return pyodbc.connect(conn_str, autocommit=False)


def verify_admin(session_token):
    """Verify if user is admin"""
    if not session_token:
        return False, None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT u.id, u.is_admin
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = %s AND s.expires_at > %s
            """,
            (session_token, datetime.utcnow()),
        )
        result = cursor.fetchone()
        conn.close()

        if result and result[1]:
            return True, result[0]
        return False, result[0] if result else None
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
            "SELECT id, name, description, price, stock, category, image_url, created_at FROM products WHERE id = %s",
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
