Key Features of ShopSphere:
1. Product Catalog Management – Add, edit, and organize products
2. Shopping Cart and Checkout – Smooth cart experience with virtual payments to simulate transactions.
3. User Authentication – Secure login/sign-up with multi-factor authentication and OAuth support.
4. Order Tracking – Real-time updates on orders and delivery status.
5. Scalability Features – Auto-scaling, CDN-backed content delivery, and load balancing to handle traffic 
spikes.
6. Wishlist and Favourites – Allows customers to save products for future purchase, enhancing 
engagement.
7. Virtual Payments Management – Simulated payment system for handling multiple virtual payment 
methods and validating transactions in a safe environment.

in ./payment and ./user-auth and ./product-catalog will be azure functions to handle payment and user auth

PRODUCT_CATALOG_URL=https://shopsphere-product-catalog-hmhxe7dzfkddhtbb.ukwest-01.azurewebsites.net/api
PAYMENT_URL=https://shopsphere-payment-esfwgag4fmfeg9eb.ukwest-01.azurewebsites.net/api
USER_AUTH_URL=https://shopsphere-user-auth-bgeqgtg5g7f3eba3.ukwest-01.azurewebsites.net/api

keep the app relatively simple. don't add unnecessary things. focus on the core features listed above.

database is at shopsphere.database.windows.net

image cdn is at https://shopsphere.blob.core.windows.net/cdn/<file>
