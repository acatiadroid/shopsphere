import json
import logging
import os
import sys

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection


def main(req: func.HttpRequest) -> func.HttpResponse:
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
            query += " AND category = %s"
            params.append(category)

        if search:
            query += " AND (name LIKE %s OR description LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([int(limit), int(offset)])

        cursor.execute(query, tuple(params))

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

        cursor.close()
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
