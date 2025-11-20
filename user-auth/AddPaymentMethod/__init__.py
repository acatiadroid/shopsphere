import json
import logging
import os
import sys
from datetime import datetime

import azure.functions as func

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.db_utils import get_db_connection, verify_session


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Add a new payment method for the user"""
    logging.info("AddPaymentMethod function triggered")

    # Verify session
    session_token = req.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = verify_session(session_token)

    if not user_id:
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=401,
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

    payment_type = req_body.get("payment_type")
    card_last_four = req_body.get("card_last_four")
    card_brand = req_body.get("card_brand")
    cardholder_name = req_body.get("cardholder_name")
    expiry_month = req_body.get("expiry_month")
    expiry_year = req_body.get("expiry_year")
    is_default = req_body.get("is_default", False)

    # Validate required fields
    if not payment_type:
        return func.HttpResponse(
            json.dumps({"error": "Payment type is required"}),
            status_code=400,
            mimetype="application/json",
        )

    # Validate payment type
    valid_types = ["credit_card", "debit_card", "paypal", "apple_pay", "google_pay"]
    if payment_type not in valid_types:
        return func.HttpResponse(
            json.dumps(
                {
                    "error": f"Invalid payment type. Valid types: {', '.join(valid_types)}"
                }
            ),
            status_code=400,
            mimetype="application/json",
        )

    # For card types, validate card details
    if payment_type in ["credit_card", "debit_card"]:
        if not card_last_four or not cardholder_name:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "Card last four digits and cardholder name are required for card payments"
                    }
                ),
                status_code=400,
                mimetype="application/json",
            )

        # Validate card_last_four is 4 digits
        if not (card_last_four.isdigit() and len(card_last_four) == 4):
            return func.HttpResponse(
                json.dumps({"error": "Card last four must be exactly 4 digits"}),
                status_code=400,
                mimetype="application/json",
            )

        # Validate expiry if provided
        if expiry_month is not None:
            try:
                month = int(expiry_month)
                if month < 1 or month > 12:
                    return func.HttpResponse(
                        json.dumps({"error": "Expiry month must be between 1 and 12"}),
                        status_code=400,
                        mimetype="application/json",
                    )
            except (ValueError, TypeError):
                return func.HttpResponse(
                    json.dumps({"error": "Invalid expiry month"}),
                    status_code=400,
                    mimetype="application/json",
                )

        if expiry_year is not None:
            try:
                year = int(expiry_year)
                if year < 2024:
                    return func.HttpResponse(
                        json.dumps({"error": "Expiry year must be 2024 or later"}),
                        status_code=400,
                        mimetype="application/json",
                    )
            except (ValueError, TypeError):
                return func.HttpResponse(
                    json.dumps({"error": "Invalid expiry year"}),
                    status_code=400,
                    mimetype="application/json",
                )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # If this is set as default, unset all other default payment methods
        if is_default:
            cursor.execute(
                "UPDATE payment_methods SET is_default = 0 WHERE user_id = ?",
                (user_id,),
            )

        # Insert the new payment method
        cursor.execute(
            """
            INSERT INTO payment_methods
            (user_id, payment_type, card_last_four, card_brand, cardholder_name, expiry_month, expiry_year, is_default, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                payment_type,
                card_last_four,
                card_brand,
                cardholder_name,
                expiry_month,
                expiry_year,
                is_default,
                datetime.utcnow(),
            ),
        )

        conn.commit()

        # Get the new payment method ID
        result = cursor.execute("SELECT @@IDENTITY").fetchone()
        payment_method_id = result[0] if result else None

        conn.close()

        if not payment_method_id:
            return func.HttpResponse(
                json.dumps({"error": "Failed to retrieve payment method ID"}),
                status_code=500,
                mimetype="application/json",
            )

        logging.info(f"Payment method {payment_method_id} added for user {user_id}")

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "payment_method_id": int(payment_method_id),
                    "message": "Payment method added successfully",
                }
            ),
            status_code=201,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Add payment method error: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
