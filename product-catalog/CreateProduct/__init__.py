import json
import logging
import os
import sys
from datetime import datetime
from decimal import Decimal

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_admin

# Try to import blob_utils, but make it optional
try:
    from shared.blob_utils import upload_image_base64
    BLOB_STORAGE_AVAILABLE = True
    logging.info("Blob storage module loaded successfully")
except Exception as e:
    logging.warning(f"Blob storage not available: {str(e)}")
    BLOB_STORAGE_AVAILABLE = False


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
        if not BLOB_STORAGE_AVAILABLE:
            logging.warning("Image data provided but blob storage module not available")
            # For now, just skip image upload and create product without image
            image_url = None
        else:
            try:
                logging.info("Uploading image to Azure Blob Storage")
                image_url = upload_image_base64(image_data, filename=name)
                logging.info(f"Image uploaded successfully: {image_url}")
            except Exception as e:
                logging.error(f"Image upload failed: {str(e)}")
                # Make image upload optional - don't fail the entire product creation
                logging.warning("Continuing product creation without image")
                image_url = None

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

        # Convert price to float if it's a Decimal (from database)
        price_value = float(price) if isinstance(price, Decimal) else price

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "product_id": int(product_id),  # Ensure it's an int, not Decimal
                    "name": name,
                    "price": price_value,
                    "image_url": image_url,
                }
            ),
            status_code=201,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Create product error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Database error: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
        )
