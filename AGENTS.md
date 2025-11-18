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

the payment function is at payment-bxehasc6bshbdpd2.norwayeast-01.azurewebsites.net
the user-auth function is at user-auth-feh2gugugngnbxbp.norwayeast-01.azurewebsites.net
product-catalog is at product-catalog-ffcjf2heceech3f6.norwayeast-01.azurewebsites.net

keep the app relatively simple. don't add unnecessary things. focus on the core features listed above.

database is at luke-shopsphere.database.windows.net

image cdn is at https://shopsphere.blob.core.windows.net/cdn/<file>
