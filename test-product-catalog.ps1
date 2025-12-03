# Test Product Catalog Function App
# Tests GetProducts endpoint

$PRODUCT_CATALOG_URL = "https://shopsphere-product-catalog-hmhxe7dzfkddhtbb.ukwest-01.azurewebsites.net/api"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Testing Product Catalog Function App" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Test: Get Products
Write-Host "Testing GetProducts..." -ForegroundColor Yellow
try {
    $productsResponse = Invoke-RestMethod -Uri "$PRODUCT_CATALOG_URL/products" -Method Get
    Write-Host "✓ Products retrieved" -ForegroundColor Green
    Write-Host "  Total products: $($productsResponse.Count)" -ForegroundColor Gray
    if ($productsResponse.Count -gt 0) {
        Write-Host "  First 3 products:" -ForegroundColor Gray
        $productsResponse | Select-Object -First 3 | ForEach-Object {
            Write-Host "  - ID: $($_.id) | $($_.name) | `$$($_.price) | Stock: $($_.stock_quantity)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "✗ Get products failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Product Catalog Testing Complete" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
