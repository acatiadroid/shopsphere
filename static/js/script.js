// Cart functionality
let cart = [];
let cartCount = 0;

// Update cart count display
function updateCartCount() {
  const cartCountElement = document.querySelector(".cart-count");
  if (cartCountElement) {
    cartCountElement.textContent = cartCount;
  }
}

// Add to cart functionality
function addToCart(productId, productName, price) {
  cart.push({ id: productId, name: productName, price: price, quantity: 1 });
  cartCount++;
  updateCartCount();
  saveCartToLocalStorage();
  showNotification(`${productName} added to cart!`);
}

// Save cart to localStorage
function saveCartToLocalStorage() {
  localStorage.setItem("cart", JSON.stringify(cart));
  localStorage.setItem("cartCount", cartCount);
}

// Load cart from localStorage
function loadCartFromLocalStorage() {
  const savedCart = localStorage.getItem("cart");
  const savedCount = localStorage.getItem("cartCount");

  if (savedCart) {
    cart = JSON.parse(savedCart);
  }
  if (savedCount) {
    cartCount = parseInt(savedCount);
    updateCartCount();
  }
}

// Show notification
function showNotification(message, type = "success") {
  const notification = document.createElement("div");
  notification.className = "notification";
  notification.textContent = message;

  const bgColor =
    type === "success" ? "#10b981" : type === "error" ? "#ef4444" : "#6366f1";

  notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: ${bgColor};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
        z-index: 9999;
        animation: slideIn 0.3s ease-out;
        font-weight: 500;
    `;

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.style.animation = "slideOut 0.3s ease-out";
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 3000);
}

// Add CSS animations
const style = document.createElement("style");
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Fetch and display categories
async function loadCategories() {
  try {
    const response = await fetch("/api/categories");
    const data = await response.json();

    if (data.success && data.categories.length > 0) {
      const categoryGrid = document.querySelector(".category-grid");
      categoryGrid.innerHTML = "";

      data.categories.forEach((category) => {
        const categoryCard = document.createElement("div");
        categoryCard.className = "category-card";
        categoryCard.innerHTML = `
                    <div class="category-icon">${category.icon || "📦"}</div>
                    <h3>${category.name}</h3>
                `;
        categoryCard.addEventListener("click", () => {
          filterProductsByCategory(category.id, category.name);
        });
        categoryGrid.appendChild(categoryCard);
      });
    }
  } catch (error) {
    console.error("Error loading categories:", error);
  }
}

// Filter products by category
function filterProductsByCategory(categoryId, categoryName) {
  showNotification(`Browsing ${categoryName} category`);
  loadProducts(categoryId);

  const productsSection = document.querySelector("#products");
  if (productsSection) {
    productsSection.scrollIntoView({ behavior: "smooth" });
  }
}

// Fetch and display products
async function loadProducts(categoryId = null) {
  try {
    let url = "/api/products";
    if (categoryId) {
      url += `?category_id=${categoryId}`;
    }

    const response = await fetch(url);
    const data = await response.json();

    if (data.success && data.products.length > 0) {
      const productGrid = document.querySelector(".product-grid");
      productGrid.innerHTML = "";

      data.products.forEach((product) => {
        const productCard = createProductCard(product);
        productGrid.appendChild(productCard);
      });

      // Re-attach event listeners
      attachProductEventListeners();
    }
  } catch (error) {
    console.error("Error loading products:", error);
    showNotification("Error loading products", "error");
  }
}

// Create product card HTML
function createProductCard(product) {
  const productCard = document.createElement("div");
  productCard.className = "product-card";

  const badgeHTML = product.badge
    ? `<div class="product-badge ${product.badge.toLowerCase()}">${product.badge}</div>`
    : "";

  const priceHTML = product.sale_price
    ? `$${product.sale_price.toFixed(2)} <del>$${product.price.toFixed(2)}</del>`
    : `$${product.price.toFixed(2)}`;

  const stars = "⭐".repeat(Math.round(product.rating));

  productCard.innerHTML = `
        ${badgeHTML}
        <div class="product-image">
            <img src="${product.image_url}" alt="${product.name}">
        </div>
        <div class="product-info">
            <h3 class="product-title">${product.name}</h3>
            <p class="product-description">${product.description}</p>
            <div class="product-rating">
                ${stars} <span>(${product.rating})</span>
            </div>
            <div class="product-footer">
                <span class="product-price">${priceHTML}</span>
                <button class="btn btn-add-cart" data-product-id="${product.id}" data-product-name="${product.name}" data-product-price="${product.sale_price || product.price}">Add to Cart</button>
            </div>
        </div>
    `;

  return productCard;
}

// Attach event listeners to product cards
function attachProductEventListeners() {
  const addToCartButtons = document.querySelectorAll(".btn-add-cart");
  addToCartButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const productId = parseInt(this.dataset.productId);
      const productName = this.dataset.productName;
      const price = parseFloat(this.dataset.productPrice);

      addToCart(productId, productName, price);
    });
  });
}

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
  // Load cart from localStorage
  loadCartFromLocalStorage();

  // Load categories and products from database
  loadCategories();
  loadProducts();

  // Cart button click
  const cartBtn = document.querySelector(".cart-btn");
  if (cartBtn) {
    cartBtn.addEventListener("click", function () {
      showCartModal();
    });
  }

  // Newsletter form submission
  const newsletterForm = document.querySelector(".newsletter-form");
  if (newsletterForm) {
    newsletterForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const emailInput = this.querySelector(".newsletter-input");
      const email = emailInput.value;

      if (email) {
        try {
          const response = await fetch("/api/newsletter/subscribe", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ email: email }),
          });

          const data = await response.json();

          if (data.success) {
            showNotification("Successfully subscribed to newsletter!");
            emailInput.value = "";
          } else {
            showNotification(data.error || "Subscription failed", "error");
          }
        } catch (error) {
          showNotification("Error subscribing to newsletter", "error");
        }
      }
    });
  }

  // Smooth scrolling for navigation links
  const navLinks = document.querySelectorAll(".nav-link");
  navLinks.forEach((link) => {
    link.addEventListener("click", function (e) {
      const href = this.getAttribute("href");
      if (href.startsWith("#")) {
        e.preventDefault();
        const target = document.querySelector(href);
        if (target) {
          target.scrollIntoView({ behavior: "smooth" });
        }

        navLinks.forEach((l) => l.classList.remove("active"));
        this.classList.add("active");
      }
    });
  });

  // Mobile menu toggle
  const mobileMenuBtn = document.querySelector(".mobile-menu-btn");
  const navMenu = document.querySelector(".nav-menu");
  if (mobileMenuBtn && navMenu) {
    mobileMenuBtn.addEventListener("click", function () {
      navMenu.classList.toggle("active");
    });
  }

  // Search button
  const searchBtn = document.querySelector(".search-btn");
  if (searchBtn) {
    searchBtn.addEventListener("click", function () {
      showSearchModal();
    });
  }
});

// Show cart modal
function showCartModal() {
  const modal = document.createElement("div");
  modal.className = "modal";

  let cartHTML = "<h2>Shopping Cart</h2>";

  if (cart.length === 0) {
    cartHTML +=
      '<p style="text-align: center; padding: 2rem; color: #6b7280;">Your cart is empty</p>';
  } else {
    cartHTML += '<div class="cart-items">';
    let total = 0;

    cart.forEach((item, index) => {
      const itemTotal = item.price * item.quantity;
      total += itemTotal;
      cartHTML += `
                <div class="cart-item" style="padding: 1rem; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${item.name}</strong>
                        <p style="color: #6b7280; font-size: 0.875rem;">$${item.price.toFixed(2)} x ${item.quantity} = $${itemTotal.toFixed(2)}</p>
                    </div>
                    <button onclick="removeFromCart(${index})" style="background: #ef4444; color: white; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer;">Remove</button>
                </div>
            `;
    });

    cartHTML += "</div>";
    cartHTML += `
            <div style="padding: 1.5rem; border-top: 2px solid #e5e7eb; margin-top: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <strong style="font-size: 1.25rem;">Total:</strong>
                    <strong style="font-size: 1.5rem; color: #6366f1;">$${total.toFixed(2)}</strong>
                </div>
                <button onclick="proceedToCheckout()" class="btn btn-primary" style="width: 100%; background: #6366f1; color: white; padding: 0.75rem;">Checkout</button>
            </div>
        `;
  }

  modal.innerHTML = `
        <div class="modal-overlay" onclick="closeModal(this)"></div>
        <div class="modal-content" style="background: white; border-radius: 12px; max-width: 500px; width: 90%; max-height: 80vh; overflow-y: auto; position: relative;">
            <button onclick="closeModal(this)" style="position: absolute; top: 1rem; right: 1rem; background: none; border: none; font-size: 1.5rem; cursor: pointer;">×</button>
            <div style="padding: 2rem;">
                ${cartHTML}
            </div>
        </div>
    `;

  modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    `;

  const overlay = modal.querySelector(".modal-overlay");
  overlay.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
    `;

  document.body.appendChild(modal);
}

// Show search modal
function showSearchModal() {
  const modal = document.createElement("div");
  modal.className = "modal";

  modal.innerHTML = `
        <div class="modal-overlay" onclick="closeModal(this)"></div>
        <div class="modal-content" style="background: white; border-radius: 12px; max-width: 600px; width: 90%; position: relative;">
            <button onclick="closeModal(this)" style="position: absolute; top: 1rem; right: 1rem; background: none; border: none; font-size: 1.5rem; cursor: pointer;">×</button>
            <div style="padding: 2rem;">
                <h2 style="margin-bottom: 1.5rem;">Search Products</h2>
                <input type="text" id="searchInput" placeholder="Search for products..." style="width: 100%; padding: 0.75rem 1rem; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 1rem; font-family: 'Poppins', sans-serif;">
                <p style="margin-top: 1rem; color: #6b7280; font-size: 0.875rem;">Try searching for headphones, watches, bags, etc.</p>
                <div id="searchResults" style="margin-top: 1rem;"></div>
            </div>
        </div>
    `;

  modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    `;

  const overlay = modal.querySelector(".modal-overlay");
  overlay.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
    `;

  document.body.appendChild(modal);

  // Focus on search input
  setTimeout(() => {
    const searchInput = modal.querySelector("#searchInput");
    searchInput.focus();

    // Add search functionality
    searchInput.addEventListener("input", async function () {
      const query = this.value.trim();
      const resultsDiv = document.getElementById("searchResults");

      if (query.length < 2) {
        resultsDiv.innerHTML = "";
        return;
      }

      try {
        const response = await fetch(
          `/api/products?search=${encodeURIComponent(query)}`,
        );
        const data = await response.json();

        if (data.success && data.products.length > 0) {
          resultsDiv.innerHTML =
            '<h3 style="margin: 1rem 0 0.5rem;">Results:</h3>';
          data.products.forEach((product) => {
            const resultItem = document.createElement("div");
            resultItem.style.cssText =
              "padding: 0.75rem; border-bottom: 1px solid #e5e7eb; cursor: pointer;";
            resultItem.innerHTML = `
                            <strong>${product.name}</strong>
                            <p style="color: #6b7280; font-size: 0.875rem;">$${(product.sale_price || product.price).toFixed(2)}</p>
                        `;
            resultItem.addEventListener("click", () => {
              closeModal(modal);
              filterProductsByCategory(
                product.category_id,
                product.category_name || "All Products",
              );
            });
            resultsDiv.appendChild(resultItem);
          });
        } else {
          resultsDiv.innerHTML =
            '<p style="color: #6b7280; margin-top: 1rem;">No products found</p>';
        }
      } catch (error) {
        console.error("Search error:", error);
      }
    });
  }, 100);
}

// Close modal
function closeModal(element) {
  const modal = element.closest ? element.closest(".modal") : element;
  if (modal) {
    modal.remove();
  }
}

// Remove item from cart
function removeFromCart(index) {
  cart.splice(index, 1);
  cartCount--;
  updateCartCount();
  saveCartToLocalStorage();
  showNotification("Item removed from cart");

  const modal = document.querySelector(".modal");
  if (modal) {
    modal.remove();
    showCartModal();
  }
}

// Proceed to checkout
async function proceedToCheckout() {
  if (cart.length === 0) {
    showNotification("Your cart is empty", "error");
    return;
  }

  // Simple checkout - in production, you'd want a proper checkout form
  const customerName = prompt("Enter your name:");
  if (!customerName) return;

  const customerEmail = prompt("Enter your email:");
  if (!customerEmail) return;

  const shippingAddress = prompt("Enter your shipping address:");
  if (!shippingAddress) return;

  try {
    const orderData = {
      customer_name: customerName,
      customer_email: customerEmail,
      shipping_address: shippingAddress,
      items: cart.map((item) => ({
        product_id: item.id,
        quantity: item.quantity,
      })),
    };

    const response = await fetch("/api/orders", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(orderData),
    });

    const data = await response.json();

    if (data.success) {
      showNotification(`Order ${data.order.order_number} placed successfully!`);

      // Clear cart
      cart = [];
      cartCount = 0;
      updateCartCount();
      saveCartToLocalStorage();

      // Close modal
      closeModal(document.querySelector(".modal"));
    } else {
      showNotification(data.error || "Order failed", "error");
    }
  } catch (error) {
    console.error("Checkout error:", error);
    showNotification("Error processing order", "error");
  }
}
