import json
import logging
import os
import sys

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_session


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Get user's transaction history"""
    logging.info("Get transactions function triggered")

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
            SELECT id, order_id, amount, payment_method, status, transaction_id, created_at
            FROM transactions
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        )

        transactions = []
        for row in cursor.fetchall():
            transactions.append(
                {
                    "id": row[0],
                    "order_id": row[1],
                    "amount": float(row[2]),
                    "payment_method": row[3],
                    "status": row[4],
                    "transaction_id": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                }
            )

        conn.close()

        return func.HttpResponse(
            json.dumps({"transactions": transactions}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Get transactions error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
