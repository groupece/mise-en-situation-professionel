#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://localhost:8000}"
EMAIL="${EMAIL:-user@example.com}"
PASSWORD="${PASSWORD:-test123}"
FILE="${FILE:-sample.pdf}"

curl -sX POST "$BASE/auth/register" -H "Content-Type: application/json" -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" >/dev/null || true
TOKEN=$(curl -sX POST "$BASE/auth/login" -H "Content-Type: application/json" -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

UP=$(curl -sX POST "$BASE/documents" -H "Authorization: Bearer $TOKEN" -F "file=@$FILE")
DOC_ID=$(python - <<'PY'
import sys, json; print(json.load(sys.stdin)["id"])
PY
<<< "$UP")

curl -sX POST "$BASE/documents/$DOC_ID/ingest" -H "Authorization: Bearer $TOKEN"

curl -s "$BASE/search?q=installation&k=3" -H "Authorization: Bearer $TOKEN" | jq '.results[0:3]'

curl -sX POST "$BASE/answers" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"question":"Comment installer ?"}' | jq '.'

curl -s "$BASE/audits" -H "Authorization: Bearer $TOKEN" | jq '.[0:5]' 