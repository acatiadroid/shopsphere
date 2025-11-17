import os
import random
from datetime import datetime

from config import Config
from main import create_app
from models import Category, Newsletter, Order, OrderItem, Product, db


def init_database():
    """Initialize database with tables and sample data"""
    print("Initializing database...")

    app = create_app()

    with app.app_context():
        # Drop all tables (use with caution in production!)
        print("Dropping existing tables...")
        db.drop_all()

        # Create all tables
        print("Creating tables...")
        db.create_all()

        # Add categories
        print("Adding categories...")
        categories = [
            Category(name="Fashion", icon="👕", description="Clothing and accessories"),
            Category(
                name="Electronics", icon="💻", description="Tech gadgets and devices"
            ),
            Category(
                name="Home & Living",
                icon="🏠",
                description="Home decor and furniture",
            ),
            Category(name="Sports", icon="⚽", description="Sports equipment and gear"),
        ]

        for category in categories:
            db.session.add(category)

        db.session.commit()
        print(f"Added {len(categories)} categories")

        # Add products
        print("Adding products...")
        products_data = [
            {
                "name": "Wireless Headphones",
                "description": "Premium noise-canceling headphones with superior sound quality and comfortable design for all-day wear",
                "price": 99.99,
                "category": "Electronics",
                "rating": 4.8,
                "review_count": 245,
                "stock_quantity": 50,
                "badge": "New",
                "image_url": "https://via.placeholder.com/300x300/6366f1/ffffff?text=Headphones",
            },
            {
                "name": "Smart Watch",
                "description": "Track your fitness and stay connected with this feature-rich smartwatch. Heart rate monitor, GPS, and more",
                "price": 149.99,
                "sale_price": 129.99,
                "category": "Electronics",
                "rating": 4.6,
                "review_count": 189,
                "stock_quantity": 35,
                "badge": "Sale",
                "image_url": "https://via.placeholder.com/300x300/8b5cf6/ffffff?text=Smart+Watch",
            },
            {
                "name": "Designer Backpack",
                "description": "Stylish and functional everyday carry bag with laptop compartment and multiple pockets",
                "price": 79.99,
                "category": "Fashion",
                "rating": 4.9,
                "review_count": 312,
                "stock_quantity": 60,
                "badge": None,
                "image_url": "https://via.placeholder.com/300x300/ec4899/ffffff?text=Backpack",
            },
            {
                "name": "Portable Speaker",
                "description": "360° sound with deep bass, waterproof design perfect for outdoor adventures",
                "price": 59.99,
                "category": "Electronics",
                "rating": 4.7,
                "review_count": 428,
                "stock_quantity": 75,
                "badge": "Hot",
                "image_url": "https://via.placeholder.com/300x300/10b981/ffffff?text=Speaker",
            },
            {
                "name": "Running Shoes",
                "description": "Lightweight and comfortable running shoes with advanced cushioning technology",
                "price": 89.99,
                "category": "Sports",
                "rating": 4.5,
                "review_count": 156,
                "stock_quantity": 42,
                "badge": None,
                "image_url": "https://via.placeholder.com/300x300/f59e0b/ffffff?text=Shoes",
            },
            {
                "name": "Coffee Maker",
                "description": "Brew perfect coffee every morning with programmable settings and thermal carafe",
                "price": 129.99,
                "category": "Home & Living",
                "rating": 4.8,
                "review_count": 201,
                "stock_quantity": 28,
                "badge": "New",
                "image_url": "https://via.placeholder.com/300x300/ef4444/ffffff?text=Coffee+Maker",
            },
            {
                "name": "Yoga Mat",
                "description": "Non-slip exercise mat with extra cushioning for comfort during workouts",
                "price": 34.99,
                "category": "Sports",
                "rating": 4.7,
                "review_count": 389,
                "stock_quantity": 100,
                "badge": None,
                "image_url": "https://via.placeholder.com/300x300/6366f1/ffffff?text=Yoga+Mat",
            },
            {
                "name": "Desk Lamp",
                "description": "Modern LED desk lamp with adjustable brightness and color temperature",
                "price": 45.99,
                "sale_price": 39.99,
                "category": "Home & Living",
                "rating": 4.6,
                "review_count": 167,
                "stock_quantity": 55,
                "badge": "Sale",
                "image_url": "https://via.placeholder.com/300x300/8b5cf6/ffffff?text=Desk+Lamp",
            },
            {
                "name": "Leather Wallet",
                "description": "Genuine leather bifold wallet with RFID protection and multiple card slots",
                "price": 49.99,
                "category": "Fashion",
                "rating": 4.8,
                "review_count": 278,
                "stock_quantity": 68,
                "badge": None,
                "image_url": "https://via.placeholder.com/300x300/ec4899/ffffff?text=Wallet",
            },
            {
                "name": "Bluetooth Earbuds",
                "description": "True wireless earbuds with crystal clear sound and long battery life",
                "price": 79.99,
                "category": "Electronics",
                "rating": 4.5,
                "review_count": 523,
                "stock_quantity": 90,
                "badge": "Hot",
                "image_url": "https://via.placeholder.com/300x300/10b981/ffffff?text=Earbuds",
            },
            {
                "name": "Water Bottle",
                "description": "Insulated stainless steel water bottle keeps drinks cold for 24 hours",
                "price": 24.99,
                "category": "Sports",
                "rating": 4.9,
                "review_count": 612,
                "stock_quantity": 150,
                "badge": None,
                "image_url": "https://via.placeholder.com/300x300/f59e0b/ffffff?text=Water+Bottle",
            },
            {
                "name": "Throw Pillow Set",
                "description": "Set of 2 decorative throw pillows with premium fabric covers",
                "price": 39.99,
                "category": "Home & Living",
                "rating": 4.7,
                "review_count": 234,
                "stock_quantity": 45,
                "badge": "New",
                "image_url": "https://via.placeholder.com/300x300/ef4444/ffffff?text=Pillows",
            },
        ]

        for product_data in products_data:
            category_name = product_data.pop("category")
            category = Category.query.filter_by(name=category_name).first()

            product = Product(
                name=product_data["name"],
                description=product_data["description"],
                price=product_data["price"],
                sale_price=product_data.get("sale_price"),
                rating=product_data["rating"],
                review_count=product_data["review_count"],
                stock_quantity=product_data["stock_quantity"],
                badge=product_data.get("badge"),
                image_url=product_data["image_url"],
                category_id=category.id if category else None,
                is_active=True,
            )
            db.session.add(product)

        db.session.commit()
        print(f"Added {len(products_data)} products")

        # Add sample newsletter subscriptions
        print("Adding sample newsletter subscriptions...")
        sample_emails = [
            "john.doe@example.com",
            "jane.smith@example.com",
            "mike.johnson@example.com",
        ]

        for email in sample_emails:
            newsletter = Newsletter(email=email, is_active=True)
            db.session.add(newsletter)

        db.session.commit()
        print(f"Added {len(sample_emails)} newsletter subscriptions")

        # Add sample orders
        print("Adding sample orders...")
        sample_orders = [
            {
                "order_number": "ORD-2024-0001",
                "customer_name": "John Doe",
                "customer_email": "john.doe@example.com",
                "customer_phone": "+1 (555) 123-4567",
                "shipping_address": "123 Main St, New York, NY 10001",
                "status": "delivered",
                "payment_status": "paid",
            },
            {
                "order_number": "ORD-2024-0002",
                "customer_name": "Jane Smith",
                "customer_email": "jane.smith@example.com",
                "customer_phone": "+1 (555) 987-6543",
                "shipping_address": "456 Oak Ave, Los Angeles, CA 90001",
                "status": "shipped",
                "payment_status": "paid",
            },
        ]

        for order_data in sample_orders:
            order = Order(**order_data, total_amount=0)
            db.session.add(order)
            db.session.flush()

            # Add random items to order
            num_items = random.randint(1, 3)
            total = 0

            for _ in range(num_items):
                product = Product.query.order_by(db.func.random()).first()
                quantity = random.randint(1, 2)
                price = product.sale_price if product.sale_price else product.price

                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    price_at_purchase=price,
                )
                db.session.add(order_item)
                total += float(price) * quantity

            order.total_amount = total

        db.session.commit()
        print(f"Added {len(sample_orders)} sample orders")

        print("\n✅ Database initialization completed successfully!")
        print(f"\nDatabase Summary:")
        print(f"  - Categories: {Category.query.count()}")
        print(f"  - Products: {Product.query.count()}")
        print(f"  - Orders: {Order.query.count()}")
        print(f"  - Newsletter Subscriptions: {Newsletter.query.count()}")


if __name__ == "__main__":
    init_database()
