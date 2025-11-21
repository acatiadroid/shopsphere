import json
import logging
import os
import sys

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_admin


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Update product (admin only)"""
    logging.info("Update product function triggered")

    product_id = req.route_params.get("id")

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
            conn.close()
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
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Product not found"}),
                status_code=404,
                mimetype="application/json",
            )

        conn.close()

        logging.info(f"Product {product_id} updated successfully")
        return func.HttpResponse(
            json.dumps({"success": True, "message": "Product updated successfully"}),
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
