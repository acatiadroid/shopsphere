import json
import logging
import os
import sys

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_session


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Get specific transaction details"""
    logging.info("Get transaction function triggered")

    transaction_id = req.route_params.get("id")

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
            WHERE id = ? AND user_id = ?
            """,
            (transaction_id, user_id),
        )

        transaction = cursor.fetchone()

        if not transaction:
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Transaction not found"}),
                status_code=404,
                mimetype="application/json",
            )

        conn.close()

        transaction_dict = {
            "id": transaction[0],
            "order_id": transaction[1],
            "amount": float(transaction[2]),
            "payment_method": transaction[3],
            "status": transaction[4],
            "transaction_id": transaction[5],
            "created_at": transaction[6].isoformat() if transaction[6] else None,
        }

        return func.HttpResponse(
            json.dumps(transaction_dict),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Get transaction error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
