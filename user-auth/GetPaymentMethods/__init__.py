import json
import logging
import os
import sys

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_session


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Get all payment methods for the authenticated user"""
    logging.info("GetPaymentMethods function triggered")

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
            SELECT id, payment_type, card_last_four, card_brand, cardholder_name,
                   expiry_month, expiry_year, is_default, created_at
            FROM payment_methods
            WHERE user_id = ?
            ORDER BY is_default DESC, created_at DESC
            """,
            (user_id,),
        )

        payment_methods = []
        for row in cursor.fetchall():
            payment_methods.append(
                {
                    "id": row[0],
                    "payment_type": row[1],
                    "card_last_four": row[2],
                    "card_brand": row[3],
                    "cardholder_name": row[4],
                    "expiry_month": row[5],
                    "expiry_year": row[6],
                    "is_default": bool(row[7]),
                    "created_at": row[8].isoformat() if row[8] else None,
                }
            )

        conn.close()

        return func.HttpResponse(
            json.dumps({"payment_methods": payment_methods}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Get payment methods error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
