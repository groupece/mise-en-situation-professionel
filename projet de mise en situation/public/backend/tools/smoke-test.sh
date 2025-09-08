#!/usr/bin/env bash
set -euo pipefail

BASE="http://127.0.0.1:8081/index.php/api"

php -S 127.0.0.1:8081 -t public >/tmp/php-server.log 2>&1 &
PHP_PID=$!
trap 'kill $PHP_PID 2>/dev/null || true' EXIT

for i in {1..30}; do
  if curl -fsS "$BASE/health" >/tmp/health.json 2>/dev/null; then
    if grep -q '"status":"ok"' /tmp/health.json && grep -q '"db":true' /tmp/health.json && grep -q '"fts":true' /tmp/health.json; then
      echo "✅ Health OK"
      break
    fi
  fi
  sleep 0.5
  if [ $i -eq 30 ]; then echo "❌ Health KO"; exit 1; fi
done

TXT="/tmp/docuhelp_$$.txt"
echo "VPN; MFA reset; mot de passe oublié; test $(date)" > "$TXT"
UPLOAD_JSON=$(curl -fsS -F "file=@${TXT};type=text/plain" "$BASE/upload")
DOC_ID=$(echo "$UPLOAD_JSON" | sed -n 's/.*"document_id":"\([^"]*\)".*/\1/p')
[ -n "$DOC_ID" ] || { echo "❌ Upload KO"; exit 1; }
echo "✅ Upload OK ($DOC_ID)"

SEARCH_JSON=$(curl -fsS -H "Content-Type: application/json" \
  -d '{"query":"mot de passe OU VPN","limit":5}' "$BASE/search")
echo "$SEARCH_JSON" | grep -q '"results":\[' || { echo "❌ Search KO"; exit 1; }
echo "$SEARCH_JSON" | grep -q '<mark>' || { echo "❌ Pas de <mark> dans snippet"; exit 1; }
echo "✅ Search OK"

SID_JSON=$(curl -fsS -X POST "$BASE/chat/session")
SID=$(echo "$SID_JSON" | sed -n 's/.*"session_id":"\([^"]*\)".*/\1/p')
[ -n "$SID" ] || { echo "❌ Chat: pas de session_id"; exit 1; }
MSG_JSON=$(curl -fsS -H "Content-Type: application/json" -d "{\"session_id\":\"$SID\",\"content\":\"Comment réinitialiser le mot de passe ?\"}" "$BASE/chat/message")
echo "$MSG_JSON" | grep -q '"top_passages":\[' || { echo "❌ Chat KO"; exit 1; }
echo "✅ Chat OK"

curl -fsS "$BASE/docs" >/dev/null || { echo "❌ Docs KO"; exit 1; }
echo "✅ Docs OK"

curl -fsS -X DELETE "$BASE/docs/$DOC_ID" >/dev/null || { echo "❌ Delete KO"; exit 1; }
echo "✅ Delete OK"

echo "✅ SMOKE TEST COMPLET"

