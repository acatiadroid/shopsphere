# ShopSphere Web Application

A modern e-commerce web application built with Flask that integrates with Azure Functions for scalable backend services.

## Architecture Overview

The webapp is a frontend Flask application that communicates with three Azure Function backends:

```
┌─────────────────┐
│   Flask WebApp  │
└────────┬────────┘
         │
         ├─────────────────────────────────────────┐
         │                                         │
         ▼                                         ▼
┌────────────────────┐                   ┌──────────────────┐
│  User Auth Service │                   │ Product Catalog  │
│  (Azure Function)  │                   │ (Azure Function) │
└────────────────────┘                   └──────────────────┘
         │                                         │
         │                                         │
         └──────────────┬──────────────────────────┘
                        ▼
                ┌───────────────────┐
                │  Payment Service  │
                │ (Azure Function)  │
                └───────────────────┘
```

## Features

1. **User Authentication** - Secure login/signup with session management
2. **Product Catalog** - Browse and search products
3. **Shopping Cart** - Add, update, and remove items
4. **Wishlist** - Save products for later
5. **Checkout & Payments** - Virtual payment processing
6. **Order Tracking** - Real-time order status updates
7. **Transaction History** - View all payment transactions

## Azure Functions Endpoints

### User Authentication Service
**Base URL:** `https://user-auth-feh2gugugngnbxbp.norwayeast-01.azurewebsites.net/api`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Register new user |
| POST | `/auth/login` | User login |
| POST | `/auth/logout` | User logout |
| POST | `/auth/verify` | Verify session token |

**Request/Response Examples:**

```json
// POST /auth/signup
Request: {
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword"
}
Response: {
  "success": true,
  "session_token": "...",
  "user": {
    "id": 123,
    "email": "john@example.com",
    "name": "John Doe",
    "is_admin": false
  }
}

// POST /auth/login
Request: {
  "email": "john@example.com",
  "password": "securepassword"
}
Response: {
  "success": true,
  "session_token": "...",
  "user": {
    "id": 123,
    "email": "john@example.com",
    "name": "John Doe",
    "is_admin": false
  }
}
```

### Product Catalog Service
**Base URL:** `https://product-catalog-ffcjf2heceech3f6.norwayeast-01.azurewebsites.net/api`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products` | Get all products |
| GET | `/products/{id}` | Get specific product |
| POST | `/products` | Create new product (admin) |
| PUT | `/products/{id}` | Update product (admin) |
| DELETE | `/products/{id}` | Delete product (admin) |
| GET | `/cart` | Get user's cart items |
| POST | `/cart` | Add item to cart |
| PUT | `/cart/{id}` | Update cart item quantity |
| DELETE | `/cart/{id}` | Remove item from cart |
| GET | `/wishlist` | Get user's wishlist |
| POST | `/wishlist` | Add item to wishlist |
| DELETE | `/wishlist/{id}` | Remove item from wishlist |

**Request/Response Examples:**

```json
// GET /products
Response: {
  "products": [
    {
      "id": 1,
      "name": "Product Name",
      "description": "...",
      "price": 29.99,
      "category": "Electronics",
      "stock_quantity": 100,
      "image_url": "https://shopsphere.blob.core.windows.net/cdn/product1.jpg"
    }
  ]
}

// POST /cart
Request: {
  "product_id": 1,
  "quantity": 2
}
Response: {
  "success": true,
  "cart_item_id": 456
}

// GET /cart
Response: {
  "items": [
    {
      "id": 456,
      "product_id": 1,
      "quantity": 2,
      "name": "Product Name",
      "price": 29.99,
      "subtotal": 59.98,
      "image_url": "...",
      "stock_quantity": 100
    }
  ]
}
```

### Payment Service
**Base URL:** `https://payment-bxehasc6bshbdpd2.norwayeast-01.azurewebsites.net/api`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/checkout` | Create order and process payment |
| POST | `/payment/process` | Process payment for order |
| GET | `/orders` | Get user's orders |
| GET | `/orders/{id}` | Get specific order details |
| GET | `/orders/{id}/track` | Track order status |
| PUT | `/orders/{id}/status` | Update order status (admin) |
| GET | `/payment/transactions` | Get user's transactions |
| GET | `/payment/transactions/{id}` | Get specific transaction |

**Request/Response Examples:**

```json
// POST /checkout
Request: {
  "payment_method": "credit_card",
  "billing_address": "123 Main St",
  "shipping_address": "123 Main St"
}
Response: {
  "success": true,
  "order_id": 789,
  "transaction_id": "TXN123456",
  "amount": 59.98
}

// GET /orders
Response: {
  "orders": [
    {
      "id": 789,
      "total_amount": 59.98,
      "status": "paid",
      "created_at": "2024-01-15T10:30:00Z",
      "paid_at": "2024-01-15T10:30:05Z"
    }
  ]
}

// GET /orders/{id}
Response: {
  "order": {
    "id": 789,
    "total_amount": 59.98,
    "status": "paid",
    "created_at": "2024-01-15T10:30:00Z",
    "paid_at": "2024-01-15T10:30:05Z"
  },
  "items": [
    {
      "product_id": 1,
      "name": "Product Name",
      "quantity": 2,
      "price": 29.99,
      "subtotal": 59.98,
      "image_url": "..."
    }
  ]
}
```

## Installation

1. **Clone the repository:**
```bash
cd shopsphere/webapp
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set environment variables:**
```bash
# Optional - defaults are already set
export SECRET_KEY="your-secret-key"
```

4. **Run the application:**
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Authentication Flow

1. User submits login/signup form
2. Webapp sends credentials to User Auth Azure Function
3. Azure Function validates and returns session token
4. Session token stored in Flask session
5. All subsequent API calls include session token in Authorization header:
   ```
   Authorization: Bearer {session_token}
   ```
6. Each request validates session via `/auth/verify` endpoint

## Project Structure

```
webapp/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── templates/            # HTML templates
    ├── base.html         # Base template with navigation
    ├── index.html        # Homepage/product listing
    ├── product_detail.html
    ├── signup.html
    ├── login.html
    ├── cart.html
    ├── wishlist.html
    ├── checkout.html
    ├── orders.html
    ├── order_detail.html
    └── transactions.html
```

## Key Components

### Session Management
- Session tokens stored in Flask session
- Automatic session verification on protected routes via `@login_required` decorator
- Sessions validated against User Auth service

### Error Handling
- All API calls wrapped in try-except blocks
- User-friendly error messages via Flask flash messages
- Graceful degradation when services are unavailable

### API Integration Helper
```python
def get_auth_headers():
    """Get authorization headers with session token"""
    if "session_token" in session:
        return {"Authorization": f"Bearer {session['session_token']}"}
    return {}
```

## CDN Integration

Product images are served from Azure Blob Storage CDN:
```
https://shopsphere.blob.core.windows.net/cdn/{filename}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| SECRET_KEY | Flask secret key for sessions | `dev-secret-key-change-in-production` |

## Development

### Running in Development Mode
```bash
export FLASK_ENV=development
python app.py
```

### Testing API Integration
All endpoints can be tested individually by checking the response from Azure Functions:
```python
import requests

# Test product listing
response = requests.get("https://product-catalog-ffcjf2heceech3f6.norwayeast-01.azurewebsites.net/api/products")
print(response.json())
```

## Security Considerations

1. **Session Tokens**: All authenticated requests include Bearer token
2. **HTTPS**: Azure Functions endpoints use HTTPS
3. **Input Validation**: All user inputs validated on backend
4. **CORS**: Configured on Azure Functions for webapp domain
5. **Password Hashing**: Handled by User Auth service (bcrypt)

## API Response Formats

### Success Response
```json
{
  "success": true,
  "data": {...}
}
```

### Error Response
```json
{
  "error": "Error message description",
  "status": 400
}
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Technologies Used

- **Flask** - Web framework
- **Bootstrap 5** - UI framework
- **Bootstrap Icons** - Icon library
- **Requests** - HTTP library for API calls
- **Azure Functions** - Serverless backend services
- **Azure Blob Storage** - CDN for static assets

## Future Enhancements

- [ ] Admin dashboard for product management
- [ ] Real-time order tracking with WebSockets
- [ ] Product reviews and ratings
- [ ] Advanced search and filtering
- [ ] Multi-currency support
- [ ] Email notifications
- [ ] OAuth integration (Google, Facebook)

## Troubleshooting

### Session Expired Errors
- Session tokens expire after inactivity
- Users automatically redirected to login page
- Clear browser cookies and login again

### API Connection Errors
- Check Azure Functions are running
- Verify network connectivity
- Check firewall settings

### Cart Not Updating
- Ensure session is valid
- Check browser console for errors
- Verify Product Catalog service is responding

## Support

For issues or questions, contact: support@shopsphere.com

## License

Copyright © 2024 ShopSphere. All rights reserved.