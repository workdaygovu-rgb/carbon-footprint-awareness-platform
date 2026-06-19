#!/usr/bin/env bash
# API Contract Sync — generates TypeScript types from the FastAPI OpenAPI schema.
#
# Usage (requires a running backend at http://localhost:8000):
#   cd frontend && npm run types:sync
#
# How it works:
#   1. Fetches the OpenAPI JSON spec from the running FastAPI backend
#   2. Generates TypeScript types using openapi-typescript
#   3. Writes the output to src/lib/generated-types.ts
#
# CI drift detection: the ci.yml workflow runs this script and checks if the
# generated types differ from the committed types.ts. If they drift apart,
# the build fails — ensuring frontend/backend schema agreement.

set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
OPENAPI_URL="${BACKEND_URL}/openapi.json"
OUTPUT_FILE="src/lib/generated-types.ts"

echo "Fetching OpenAPI spec from ${OPENAPI_URL}..."
if ! curl -sf "${OPENAPI_URL}" -o /tmp/openapi.json; then
  echo "ERROR: Could not reach ${OPENAPI_URL}. Is the backend running?"
  echo "Start it with: cd ../backend && USE_GEMINI=false USE_FIRESTORE=false uvicorn app.main:app"
  exit 1
fi

echo "Generating TypeScript types..."
npx -y openapi-typescript /tmp/openapi.json -o "${OUTPUT_FILE}"

echo "Types written to ${OUTPUT_FILE}"
echo "Compare with src/lib/types.ts to check for drift."
