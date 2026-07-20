#!/usr/bin/env bash
set -euo pipefail

# Generate client SDK from OpenAPI spec
# Usage: ./scripts/generate-client.sh [language] [output_dir]
# Examples:
#   ./scripts/generate-client.sh typescript-axios ./clients/typescript
#   ./scripts/generate-client.sh python ./clients/python
#   ./scripts/generate-client.sh go ./clients/go

LANGUAGE="${1:-typescript-axios}"
OUTPUT_DIR="${2:-./clients/$LANGUAGE}"
API_URL="${API_URL:-http://localhost:8000/openapi.json}"

echo "Generating $LANGUAGE client from $API_URL..."

# Check if openapi-generator is installed
if ! command -v openapi-generator-cli &> /dev/null; then
    echo "Installing openapi-generator-cli..."
    npm install -g @openapi-generator/cli
fi

openapi-generator-cli generate \
    -i "$API_URL" \
    -g "$LANGUAGE" \
    -o "$OUTPUT_DIR" \
    --skip-validate-spec

echo "Client generated at $OUTPUT_DIR"
