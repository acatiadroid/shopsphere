# Test User Authentication Function App
# Tests Login endpoint

$USER_AUTH_URL = "https://shopsphere-user-auth-bgeqgtg5g7f3eba3.ukwest-01.azurewebsites.net/api"

# Configuration - Update these with your test user credentials
$TEST_EMAIL = "john@gmail.com"
$TEST_PASSWORD = "Password1%"

$loginBody = @{
    email = $TEST_EMAIL
    password = $TEST_PASSWORD
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "$USER_AUTH_URL/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
    Write-Host "✓ Login successful" -ForegroundColor Green
    Write-Host "  User ID: $($loginResponse.user.id)" -ForegroundColor Gray
    Write-Host "  Email: $($loginResponse.user.email)" -ForegroundColor Gray
    Write-Host "  Name: $($loginResponse.user.name)" -ForegroundColor Gray
    Write-Host "  Session Token: $($loginResponse.session_token.Substring(0, 30))..." -ForegroundColor Gray
} catch {
    Write-Host "✗ Login failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
Write-Host ""
