# Test User Authentication Function App
# Tests Signup endpoint

$USER_AUTH_URL = "https://shopsphere-user-auth-bgeqgtg5g7f3eba3.ukwest-01.azurewebsites.net/api"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Testing User Auth Function App" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Test: Signup
Write-Host "Testing Signup..." -ForegroundColor Yellow
$signupBody = @{
    email = "testuser$(Get-Random -Minimum 1000 -Maximum 9999)@example.com"
    password = "Test123!@#"
    name = "Test User"
} | ConvertTo-Json

try {
    $signupResponse = Invoke-RestMethod -Uri "$USER_AUTH_URL/signup" -Method Post -Body $signupBody -ContentType "application/json"
    Write-Host "✓ Signup successful" -ForegroundColor Green
    Write-Host "  User ID: $($signupResponse.user_id)" -ForegroundColor Gray
    Write-Host "  Email: $($signupResponse.email)" -ForegroundColor Gray
    Write-Host "  Name: $($signupResponse.name)" -ForegroundColor Gray
    Write-Host "  Session Token: $($signupResponse.session_token.Substring(0, 30))..." -ForegroundColor Gray
} catch {
    Write-Host "✗ Signup failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "User Auth Testing Complete" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
