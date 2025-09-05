Param(
  [string]$Base = "http://localhost:8000",
  [string]$Email = "user@example.com",
  [string]$Password = "test123",
  [string]$FilePath = "sample.pdf"
)

Write-Host "Register..."
try { Invoke-RestMethod -Uri "$Base/auth/register" -Method POST -ContentType "application/json" -Body (@{ email=$Email; password=$Password } | ConvertTo-Json) | Out-Null } catch {}

Write-Host "Login..."
$login = Invoke-RestMethod -Uri "$Base/auth/login" -Method POST -ContentType "application/json" -Body (@{ email=$Email; password=$Password } | ConvertTo-Json)
$TOKEN = $login.access_token

Write-Host "Upload..."
$upload = Invoke-RestMethod -Uri "$Base/documents" -Method POST -Headers @{ Authorization = "Bearer $TOKEN" } -Form @{ file = Get-Item $FilePath }
$DOC_ID = $upload.id

Write-Host "Ingest..."
$ing = Invoke-RestMethod -Uri "$Base/documents/$DOC_ID/ingest" -Method POST -Headers @{ Authorization = "Bearer $TOKEN" }

Write-Host "Search..."
$search = Invoke-RestMethod -Uri "$Base/search?q=installation&k=3" -Method GET -Headers @{ Authorization = "Bearer $TOKEN" }

Write-Host "Answers..."
$ans = Invoke-RestMethod -Uri "$Base/answers" -Method POST -Headers @{ Authorization = "Bearer $TOKEN" } -ContentType "application/json" -Body (@{ question = "Comment installer ?" } | ConvertTo-Json)

Write-Host "Audits..."
$aud = Invoke-RestMethod -Uri "$Base/audits" -Method GET -Headers @{ Authorization = "Bearer $TOKEN" }

$summary = [ordered]@{
  upload = $upload
  ingest = $ing
  search = $search
  answers = $ans
  audits = ($aud | Select-Object -First 5)
}
$summary | ConvertTo-Json -Depth 6 