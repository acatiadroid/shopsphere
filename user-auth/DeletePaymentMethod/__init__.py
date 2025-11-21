import json
import logging
import os
import sys

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_session


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Delete a payment method"""
    logging.info("DeletePaymentMethod function triggered")

    session_token = req.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = verify_session(session_token)

    if not user_id:
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=401,
            mimetype="application/json",
        )

    payment_method_id = req.route_params.get("id")

    if not payment_method_id:
        return func.HttpResponse(
            json.dumps({"error": "Payment method ID is required"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM payment_methods WHERE id = ? AND user_id = ?",
            (payment_method_id, user_id),
        )

        if not cursor.fetchone():
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "Payment method not found"}),
                status_code=404,
                mimetype="application/json",
            )

        cursor.execute(
            "DELETE FROM payment_methods WHERE id = ? AND user_id = ?",
            (payment_method_id, user_id),
        )

        conn.commit()
        conn.close()

        logging.info(f"Payment method {payment_method_id} deleted for user {user_id}")
        return func.HttpResponse(
            json.dumps({"success": True, "message": "Payment method deleted"}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Delete payment method error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
