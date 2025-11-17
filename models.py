from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Category(db.Model):
    """Category model for product categorization"""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    icon = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with products
    products = db.relationship("Product", backref="category", lazy=True)

    def to_dict(self):
        """Convert category to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "description": self.description,
        }


class Product(db.Model):
    """Product model for shop items"""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    sale_price = db.Column(db.Numeric(10, 2), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    rating = db.Column(db.Numeric(2, 1), default=0.0)
    review_count = db.Column(db.Integer, default=0)
    stock_quantity = db.Column(db.Integer, default=0)
    badge = db.Column(db.String(50), nullable=True)  # 'New', 'Sale', 'Hot', etc.
    is_active = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship with order items
    order_items = db.relationship("OrderItem", backref="product", lazy=True)

    def to_dict(self):
        """Convert product to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "sale_price": float(self.sale_price) if self.sale_price else None,
            "image_url": self.image_url,
            "rating": float(self.rating),
            "review_count": self.review_count,
            "stock_quantity": self.stock_quantity,
            "badge": self.badge,
            "is_active": self.is_active,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
        }


class Order(db.Model):
    """Order model for customer purchases"""

    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(200), nullable=False)
    customer_email = db.Column(db.String(200), nullable=False)
    customer_phone = db.Column(db.String(50), nullable=True)
    shipping_address = db.Column(db.Text, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(
        db.String(50), default="pending"
    )  # pending, processing, shipped, delivered, cancelled
    payment_status = db.Column(
        db.String(50), default="pending"
    )  # pending, paid, failed, refunded
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship with order items
    order_items = db.relationship(
        "OrderItem", backref="order", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Convert order to dictionary"""
        return {
            "id": self.id,
            "order_number": self.order_number,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "customer_phone": self.customer_phone,
            "shipping_address": self.shipping_address,
            "total_amount": float(self.total_amount),
            "status": self.status,
            "payment_status": self.payment_status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "items": [item.to_dict() for item in self.order_items],
        }


class OrderItem(db.Model):
    """OrderItem model for individual items in an order"""

    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_at_purchase = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert order item to dictionary"""
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "quantity": self.quantity,
            "price_at_purchase": float(self.price_at_purchase),
            "subtotal": float(self.price_at_purchase * self.quantity),
        }


class Newsletter(db.Model):
    """Newsletter subscription model"""

    __tablename__ = "newsletter_subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert newsletter subscription to dictionary"""
        return {
            "id": self.id,
            "email": self.email,
            "is_active": self.is_active,
            "subscribed_at": self.subscribed_at.isoformat()
            if self.subscribed_at
            else None,
        }
