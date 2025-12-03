# Test Payment Function App
# Tests GetTransactions endpoint

$PAYMENT_URL = "https://shopsphere-payment-esfwgag4fmfeg9eb.ukwest-01.azurewebsites.net/api"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Testing Payment Function App" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Test: Get Transactions
Write-Host "Testing GetTransactions..." -ForegroundColor Yellow
Write-Host "Note: Enter a user_id to test, or press Enter to use sample ID (1)" -ForegroundColor Gray
$inputUserId = Read-Host "User ID"

if ([string]::IsNullOrWhiteSpace($inputUserId)) {
    $inputUserId = 1
    Write-Host "Using sample user_id: $inputUserId" -ForegroundColor Gray
}

try {
    $transactionsResponse = Invoke-RestMethod -Uri "$PAYMENT_URL/transactions/$inputUserId" -Method Get
    Write-Host "✓ Transactions retrieved" -ForegroundColor Green
    Write-Host "  Total transactions: $($transactionsResponse.Count)" -ForegroundColor Gray
    if ($transactionsResponse.Count -gt 0) {
        Write-Host "  Transactions:" -ForegroundColor Gray
        foreach ($transaction in $transactionsResponse) {
            Write-Host "  - ID: $($transaction.id) | Amount: `$$($transaction.amount) | Status: $($transaction.status) | Method: $($transaction.payment_method)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  No transactions found for this user" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Get transactions failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Payment Testing Complete" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
$USER_AUTH_URL = "https://shopsphere-user-auth-bgeqgtg5g7f3eba3.ukwest-01.azurewebsites.net/api"
$PRODUCT_CATALOG_URL = "https://shopsphere-product-catalog-hmhxe7dzfkddhtbb.ukwest-01.azurewebsites.net/api"

# Create user
$signupBody = @{
    email = "paymenttest$(Get-Random -Minimum 1000 -Maximum 9999)@example.com"
    password = "Test123!@#"
    name = "Payment Test User"
} | ConvertTo-Json

try {
    $userResponse = Invoke-RestMethod -Uri "$USER_AUTH_URL/signup" -Method Post -Body $signupBody -ContentType "application/json"
    $userId = $userResponse.user_id
    Write-Host "✓ Test user created (ID: $userId)" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to create test user: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Create product
$createProductBody = @{
    name = "Payment Test Product $(Get-Random -Minimum 1000 -Maximum 9999)"
    description = "Product for payment testing"
    price = 49.99
    stock_quantity = 50
    category = "Test"
    image_url = "https://shopsphere.blob.core.windows.net/cdn/test.jpg"
} | ConvertTo-Json

try {
    $productResponse = Invoke-RestMethod -Uri "$PRODUCT_CATALOG_URL/products" -Method Post -Body $createProductBody -ContentType "application/json"
    $productId = $productResponse.id
    Write-Host "✓ Test product created (ID: $productId)" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to create test product: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Add to cart
$addCartBody = @{
    user_id = $userId
    product_id = $productId
    quantity = 3
} | ConvertTo-Json

try {
    Invoke-RestMethod -Uri "$PRODUCT_CATALOG_URL/cart" -Method Post -Body $addCartBody -ContentType "application/json" | Out-Null
    Write-Host "✓ Product added to cart" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to add to cart: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 1: Checkout
Write-Host "[1/5] Testing Checkout..." -ForegroundColor Yellow
$checkoutBody = @{
    user_id = $userId
} | ConvertTo-Json

try {
    $checkoutResponse = Invoke-RestMethod -Uri "$PAYMENT_URL/checkout" -Method Post -Body $checkoutBody -ContentType "application/json"
    Write-Host "✓ Checkout successful" -ForegroundColor Green
    Write-Host "  Total Amount: `$$($checkoutResponse.total_amount)" -ForegroundColor Gray
    Write-Host "  Items: $($checkoutResponse.items.Count)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Checkout failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: Process Payment
Write-Host "[2/5] Testing ProcessPayment..." -ForegroundColor Yellow
$paymentBody = @{
    user_id = $userId
    payment_method = "credit_card"
    shipping_address = "123 Test St, Test City, TC 12345"
} | ConvertTo-Json

try {
    $paymentResponse = Invoke-RestMethod -Uri "$PAYMENT_URL/process-payment" -Method Post -Body $paymentBody -ContentType "application/json"
    Write-Host "✓ Payment processed" -ForegroundColor Green
    Write-Host "  Order ID: $($paymentResponse.order_id)" -ForegroundColor Gray
    Write-Host "  Tracking Number: $($paymentResponse.tracking_number)" -ForegroundColor Gray
    Write-Host "  Status: $($paymentResponse.status)" -ForegroundColor Gray
    $orderId = $paymentResponse.order_id
    $trackingNumber = $paymentResponse.tracking_number
} catch {
    Write-Host "✗ Payment processing failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 3: Get Orders
Write-Host "[3/5] Testing GetOrders..." -ForegroundColor Yellow
try {
    $ordersResponse = Invoke-RestMethod -Uri "$PAYMENT_URL/orders/$userId" -Method Get
    Write-Host "✓ Orders retrieved" -ForegroundColor Green
    Write-Host "  Total orders: $($ordersResponse.Count)" -ForegroundColor Gray
    foreach ($order in $ordersResponse) {
        Write-Host "  - Order #$($order.id): `$$($order.total_amount) ($($order.status))" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Get orders failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 4: Track Order
Write-Host "[4/5] Testing TrackOrder..." -ForegroundColor Yellow
try {
    $trackResponse = Invoke-RestMethod -Uri "$PAYMENT_URL/track-order/$trackingNumber" -Method Get
    Write-Host "✓ Order tracked" -ForegroundColor Green
    Write-Host "  Order ID: $($trackResponse.id)" -ForegroundColor Gray
    Write-Host "  Status: $($trackResponse.status)" -ForegroundColor Gray
    Write-Host "  Total: `$$($trackResponse.total_amount)" -ForegroundColor Gray
    Write-Host "  Created: $($trackResponse.created_at)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Track order failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 5: Get Transactions
Write-Host "[5/5] Testing GetTransactions..." -ForegroundColor Yellow
try {
    $transactionsResponse = Invoke-RestMethod -Uri "$PAYMENT_URL/transactions/$userId" -Method Get
    Write-Host "✓ Transactions retrieved" -ForegroundColor Green
    Write-Host "  Total transactions: $($transactionsResponse.Count)" -ForegroundColor Gray
    foreach ($transaction in $transactionsResponse) {
        Write-Host "  - Transaction #$($transaction.id): `$$($transaction.amount) ($($transaction.status))" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Get transactions failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Payment Testing Complete" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
