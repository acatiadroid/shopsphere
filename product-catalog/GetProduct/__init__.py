import json
import logging
import os
import sys

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Get single product by ID"""
    logging.info("Get product function triggered")

    product_id = req.route_params.get("id")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, name, description, price, stock_quantity, category, image_url, created_at FROM products WHERE id = %s",
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

        cursor.close()
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
