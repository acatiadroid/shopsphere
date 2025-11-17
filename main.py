from datetime import datetime

from flask import Flask, jsonify, render_template, request

from config import Config
from models import Category, Newsletter, Order, OrderItem, Product, db


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    return app


app = create_app()


# ============= Web Routes =============


@app.route("/")
def home():
    """Render the main shop page"""
    return render_template("index.html")


# ============= API Routes =============


@app.route("/api/categories", methods=["GET"])
def get_categories():
    """Get all categories"""
    try:
        categories = Category.query.all()
        return jsonify(
            {"success": True, "categories": [cat.to_dict() for cat in categories]}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/products", methods=["GET"])
def get_products():
    """Get all active products with optional filtering"""
    try:
        # Get query parameters
        category_id = request.args.get("category_id", type=int)
        search_query = request.args.get("search", "")
        limit = request.args.get("limit", type=int)

        # Build query
        query = Product.query.filter_by(is_active=True)

        # Apply filters
        if category_id:
            query = query.filter_by(category_id=category_id)

        if search_query:
            query = query.filter(
                Product.name.ilike(f"%{search_query}%")
                | Product.description.ilike(f"%{search_query}%")
            )

        # Apply limit if specified
        if limit:
            query = query.limit(limit)

        products = query.all()

        return jsonify(
            {
                "success": True,
                "products": [product.to_dict() for product in products],
                "count": len(products),
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """Get a single product by ID"""
    try:
        product = Product.query.get_or_404(product_id)
        return jsonify({"success": True, "product": product.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 404


@app.route("/api/products/featured", methods=["GET"])
def get_featured_products():
    """Get featured products (products with badges)"""
    try:
        products = (
            Product.query.filter(Product.is_active, Product.badge.isnot(None))
            .limit(6)
            .all()
        )

        return jsonify(
            {"success": True, "products": [product.to_dict() for product in products]}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/orders", methods=["POST"])
def create_order():
    """Create a new order"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = [
            "customer_name",
            "customer_email",
            "shipping_address",
            "items",
        ]
        for field in required_fields:
            if field not in data:
                return jsonify(
                    {"success": False, "error": f"Missing required field: {field}"}
                ), 400

        # Generate order number
        order_count = Order.query.count()
        order_number = f"ORD-{datetime.now().year}-{order_count + 1:04d}"

        # Create order
        order = Order(
            order_number=order_number,
            customer_name=data["customer_name"],
            customer_email=data["customer_email"],
            customer_phone=data.get("customer_phone"),
            shipping_address=data["shipping_address"],
            notes=data.get("notes"),
            total_amount=0,
            status="pending",
            payment_status="pending",
        )

        db.session.add(order)
        db.session.flush()

        # Add order items and calculate total
        total = 0
        for item_data in data["items"]:
            product = Product.query.get(item_data["product_id"])
            if not product:
                db.session.rollback()
                return jsonify(
                    {
                        "success": False,
                        "error": f"Product {item_data['product_id']} not found",
                    }
                ), 404

            # Check stock
            if product.stock_quantity < item_data["quantity"]:
                db.session.rollback()
                return jsonify(
                    {
                        "success": False,
                        "error": f"Insufficient stock for {product.name}",
                    }
                ), 400

            price = product.sale_price if product.sale_price else product.price

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item_data["quantity"],
                price_at_purchase=price,
            )
            db.session.add(order_item)

            total += float(price) * item_data["quantity"]

            # Update stock
            product.stock_quantity -= item_data["quantity"]

        order.total_amount = total
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "order": order.to_dict(),
                "message": "Order created successfully",
            }
        ), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    """Get order details"""
    try:
        order = Order.query.get_or_404(order_id)
        return jsonify({"success": True, "order": order.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 404


@app.route("/api/newsletter/subscribe", methods=["POST"])
def subscribe_newsletter():
    """Subscribe to newsletter"""
    try:
        data = request.get_json()

        if "email" not in data:
            return jsonify({"success": False, "error": "Email is required"}), 400

        # Check if already subscribed
        existing = Newsletter.query.filter_by(email=data["email"]).first()
        if existing:
            if existing.is_active:
                return jsonify(
                    {"success": False, "error": "Email already subscribed"}
                ), 400
            else:
                # Reactivate subscription
                existing.is_active = True
                db.session.commit()
                return jsonify(
                    {
                        "success": True,
                        "message": "Subscription reactivated successfully",
                    }
                )

        # Create new subscription
        subscription = Newsletter(email=data["email"], is_active=True)
        db.session.add(subscription)
        db.session.commit()

        return jsonify(
            {"success": True, "message": "Successfully subscribed to newsletter"}
        ), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get shop statistics"""
    try:
        stats = {
            "total_products": Product.query.filter_by(is_active=True).count(),
            "total_categories": Category.query.count(),
            "total_orders": Order.query.count(),
            "newsletter_subscribers": Newsletter.query.filter_by(
                is_active=True
            ).count(),
        }
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============= Error Handlers =============


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Resource not found"}), 404
    return render_template("index.html"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Internal server error"}), 500
    return "Internal Server Error", 500


# ============= Database Commands =============


@app.cli.command()
def init_db():
    """Initialize the database with tables"""
    db.create_all()
    print("Database tables created successfully!")


@app.cli.command()
def seed_db():
    """Seed the database with sample data"""
    from init_db import init_database

    init_database()


if __name__ == "__main__":
    app.run(debug=True)
