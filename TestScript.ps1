
# Set base URL
$baseUrl = "https://user-auth-feh2gugugngnbxbp.norwayeast-01.azurewebsites.net/api/auth"

# Test Signup
Write-Host "=== Testing Signup ===" -ForegroundColor Cyan
$signupBody = @{
    email = "testuser@example.com"
    password = "TestPassword123!"
    name = "Test User"
} | ConvertTo-Json

$signupResponse = Invoke-RestMethod -Uri "$baseUrl/signup" -Method Post -Body $signupBody -ContentType "application/json"
$signupResponse | ConvertTo-Json
$sessionToken = $signupResponse.session_token

# Test Login
Write-Host "`n=== Testing Login ===" -ForegroundColor Cyan
$loginBody = @{
    email = "testuser@example.com"
    password = "TestPassword123!"
} | ConvertTo-Json

$loginResponse = Invoke-RestMethod -Uri "$baseUrl/login" -Method Post -Body $loginBody -ContentType "application/json"
$loginResponse | ConvertTo-Json

# Test VerifySession
Write-Host "`n=== Testing VerifySession ===" -ForegroundColor Cyan
$verifyBody = @{
    session_token = $sessionToken
} | ConvertTo-Json

$verifyResponse = Invoke-RestMethod -Uri "$baseUrl/verifysession" -Method Post -Body $verifyBody -ContentType "application/json"
$verifyResponse | ConvertTo-Json
