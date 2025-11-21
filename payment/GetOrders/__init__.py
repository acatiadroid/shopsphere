import json
import logging
import os
import sys

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_session


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Get user's orders"""
    logging.info("Get orders function triggered")

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
            json.dumps({"orders": orders}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Get orders error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
