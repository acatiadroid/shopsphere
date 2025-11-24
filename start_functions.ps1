# ShopSphere - Start All Azure Functions Locally
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  ShopSphere Azure Functions" -ForegroundColor Cyan  
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# MySQL connection string - UPDATE THIS WITH YOUR PASSWORD!
$mysqlConnStr = "DRIVER={MySQL ODBC 8.0 Driver};SERVER=localhost;PORT=3306;DATABASE=shopsphere_db;UID=root;PWD=password"

Write-Host "Creating/updating local.settings.json files..." -ForegroundColor Yellow

# User Auth
$userAuthSettings = @"
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "SqlConnectionString": "$mysqlConnStr"
  }
}
"@
$userAuthSettings | Out-File -FilePath "user-auth/local.settings.json" -Encoding utf8 -Force
Write-Host "  ✓ user-auth/local.settings.json updated" -ForegroundColor Green

# Product Catalog  
$productSettings = @"
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "SqlConnectionString": "$mysqlConnStr",
    "AZURE_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https;AccountName=shopsphere;AccountKey=your_key_here;EndpointSuffix=core.windows.net"
  }
}
"@
$productSettings | Out-File -FilePath "product-catalog/local.settings.json" -Encoding utf8 -Force
Write-Host "  ✓ product-catalog/local.settings.json updated" -ForegroundColor Green

# Payment
$paymentSettings = @"
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "SqlConnectionString": "$mysqlConnStr"
  }
}
"@
$paymentSettings | Out-File -FilePath "payment/local.settings.json" -Encoding utf8 -Force
Write-Host "  ✓ payment/local.settings.json updated" -ForegroundColor Green

Write-Host ""
Write-Host "Starting Azure Functions..." -ForegroundColor Cyan
Write-Host "User Auth:       http://localhost:7071" -ForegroundColor Green
Write-Host "Product Catalog: http://localhost:7072" -ForegroundColor Green
Write-Host "Payment:         http://localhost:7073" -ForegroundColor Green
Write-Host ""

# Start functions
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd user-auth; Write-Host 'User Auth - Port 7071' -ForegroundColor Cyan; func start --port 7071"
Start-Sleep -Seconds 1
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd product-catalog; Write-Host 'Product Catalog - Port 7072' -ForegroundColor Cyan; func start --port 7072"
Start-Sleep -Seconds 1
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd payment; Write-Host 'Payment - Port 7073' -ForegroundColor Cyan; func start --port 7073"

Write-Host ""
Write-Host "All functions started!" -ForegroundColor Green
