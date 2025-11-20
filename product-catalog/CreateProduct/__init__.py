import json
import logging
import os
import sys
from datetime import datetime

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.blob_utils import upload_image_base64
from shared.db_utils import get_db_connection, verify_admin


def main(req: func.HttpRequest) -> func.HttpResponse:
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
    image_data = req_body.get("image_data")  # Base64 encoded image

    if not name or not price or not category:
        return func.HttpResponse(
            json.dumps({"error": "Name, price, and category are required"}),
            status_code=400,
            mimetype="application/json",
        )

    # Handle image upload if base64 data is provided
    if image_data:
        try:
            logging.info("Uploading image to Azure Blob Storage")
            image_url = upload_image_base64(image_data, filename=name)
            logging.info(f"Image uploaded: {image_url}")
        except Exception as e:
            logging.error(f"Image upload failed: {str(e)}")
            return func.HttpResponse(
                json.dumps({"error": f"Image upload failed: {str(e)}"}),
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
                    "image_url": image_url,
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
