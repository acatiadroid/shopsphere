# Test Product Catalog Function App
# Tests GetProducts endpoint

$PRODUCT_CATALOG_URL = "https://shopsphere-product-catalog-hmhxe7dzfkddhtbb.ukwest-01.azurewebsites.net/api"

Write-Host ""

# Test: Get Products
Write-Host "Testing GetProducts..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$PRODUCT_CATALOG_URL/products" -Method Get
    $products = $response.products
    Write-Host "✓ Products retrieved" -ForegroundColor Green
    Write-Host "  Total products: $($products.Count)" -ForegroundColor Gray
    Write-Host ""
    
    if ($products.Count -gt 0) {
        Write-Host "Product Catalog:" -ForegroundColor Cyan
        Write-Host ("-" * 100) -ForegroundColor Gray
        foreach ($product in $products) {
            Write-Host "ID: $($product.id)" -ForegroundColor White
            Write-Host "  Name: $($product.name)" -ForegroundColor Yellow
            Write-Host "  Description: $($product.description)" -ForegroundColor Gray
            Write-Host "  Price: `$$($product.price)" -ForegroundColor Green
            Write-Host "  Category: $($product.category)" -ForegroundColor Cyan
            Write-Host "  Stock: $($product.stock_quantity)" -ForegroundColor Magenta
            if ($product.image_url) {
                Write-Host "  Image: $($product.image_url)" -ForegroundColor DarkGray
            }
            Write-Host ("-" * 100) -ForegroundColor Gray
        }
    } else {
        Write-Host "  No products found in catalog" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Get products failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
Write-Host ""
