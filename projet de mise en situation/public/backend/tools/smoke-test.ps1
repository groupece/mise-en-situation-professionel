Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$BaseUrl = "http://127.0.0.1:8081/index.php/api"

function Write-OK($msg){ Write-Host "✅ $msg" }
function Write-FAIL($msg){ Write-Host "❌ $msg"; exit 1 }

Write-Host "🚀 Démarrage serveur PHP…"
$proc = Start-Process -FilePath "php" -ArgumentList "-S 127.0.0.1:8081 -t public" -WorkingDirectory "." -PassThru
Start-Sleep -Seconds 1

try {
  $ready = $false
  for ($i=0; $i -lt 30; $i++) {
    try {
      $health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method GET -TimeoutSec 2
      if ($health.status -eq "ok" -and $health.db -eq $true -and $health.fts -eq $true) { $ready = $true; break }
    } catch { Start-Sleep -Milliseconds 500 }
  }
  if (-not $ready) { Write-FAIL "Health check KO (timeout)" }
  Write-OK "Health check OK ($($health | ConvertTo-Json -Compress))"

  if (Test-Path ".\vendor\bin\phpunit") {
    Write-Host "🧪 Lancement PHPUnit…"
    & .\vendor\bin\phpunit | Write-Host
  }

  $tmp = [System.IO.Path]::GetTempFileName()
  [System.IO.File]::WriteAllText($tmp, "VPN configuration; reset MFA; mot de passe oublié; accès intranet; test DocuHelp $(Get-Date).")

  Write-Host "⬆️  Upload TXT…"
  $upload = Invoke-RestMethod -Uri "$BaseUrl/upload" -Method POST -Form @{ file = Get-Item $tmp }
  if (-not $upload.document_id) { Write-FAIL "Upload: pas de document_id" }
  $docId = $upload.document_id
  Write-OK "Upload OK (docId=$docId, pages=$($upload.page_count))"

  Write-Host "🔎 Recherche…"
  $searchBody = @{ query = "mot de passe OU VPN"; limit = 5 } | ConvertTo-Json
  $search = Invoke-RestMethod -Uri "$BaseUrl/search" -Method POST -ContentType "application/json" -Body $searchBody
  if (-not $search.results -or $search.results.Count -lt 1) { Write-FAIL "Search: aucun résultat" }
  if ($search.results[0].snippet -notmatch "<mark>") { Write-FAIL "Search: pas de balises <mark> dans le snippet" }
  Write-OK "Search OK (n=$($search.results.Count))"

  Write-Host "💬 Chat session…"
  $sid = (Invoke-RestMethod -Uri "$BaseUrl/chat/session" -Method POST).session_id
  if (-not $sid) { Write-FAIL "Chat: session_id manquant" }
  $msgBody = @{ session_id = $sid; content = "Comment réinitialiser le mot de passe ?" } | ConvertTo-Json
  $reply = Invoke-RestMethod -Uri "$BaseUrl/chat/message" -Method POST -ContentType "application/json" -Body $msgBody
  if (-not $reply.top_passages -or $reply.top_passages.Count -lt 1) { Write-FAIL "Chat: aucun passage retourné" }
  Write-OK "Chat OK (passages=$($reply.top_passages.Count))"

  $docs = Invoke-RestMethod -Uri "$BaseUrl/docs" -Method GET
  if (-not $docs.items) { Write-FAIL "Docs: liste vide" }
  Write-OK "Docs OK (n=$($docs.items.Count))"

  Write-Host "🗑️  Suppression document…"
  $del = Invoke-RestMethod -Uri "$BaseUrl/docs/$docId" -Method DELETE
  Write-OK "Delete OK"

  Write-Host ""
  Write-OK "SMOKE TEST COMPLET ✅"
}
finally {
  if ($proc -and !$proc.HasExited) {
    Stop-Process -Id $proc.Id -Force
    Write-Host "🛑 Serveur PHP arrêté."
  }
}

