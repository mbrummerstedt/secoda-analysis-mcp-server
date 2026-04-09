#!/usr/bin/env bash
# build.sh — builds the Miinto-specific .mcpb bundle
# Requires: bundle/manifest.json (gitignored, contains org credentials)
# Output:   dist/miinto-secoda-analyst.mcpb
#
# The .mcpb is a zip with manifest.json at the root. For uv server type,
# we include pyproject.toml and the source package so the host can run
# `uv run python -m secoda_analysis_mcp.server` directly.

set -euo pipefail

BUNDLE_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$BUNDLE_DIR")"
DIST_DIR="$REPO_ROOT/dist"
OUTPUT="$DIST_DIR/miinto-secoda-analyst.mcpb"
STAGING="$REPO_ROOT/.bundle-staging"

if [ ! -f "$BUNDLE_DIR/manifest.json" ]; then
  echo "Error: bundle/manifest.json not found."
  echo "Copy bundle/manifest.template.json to bundle/manifest.json and fill in your org credentials."
  exit 1
fi

mkdir -p "$DIST_DIR"

# Stage files with the flat structure the host expects
rm -rf "$STAGING"
mkdir -p "$STAGING"

cp "$BUNDLE_DIR/manifest.json" "$STAGING/"
cp "$REPO_ROOT/pyproject.toml" "$STAGING/"
cp -r "$REPO_ROOT/src/secoda_analysis_mcp" "$STAGING/secoda_analysis_mcp"
cp -r "$BUNDLE_DIR/server" "$STAGING/server"
[ -f "$BUNDLE_DIR/README.md" ] && cp "$BUNDLE_DIR/README.md" "$STAGING/"

cd "$STAGING"
zip -r "$OUTPUT" .

rm -rf "$STAGING"

echo ""
echo "Bundle created: $OUTPUT"
echo ""
echo "To install:"
echo "  1. Open Claude Desktop → Settings → Developer"
echo "  2. Drag and drop $OUTPUT onto the window"
echo "  OR"
echo "  3. Share $OUTPUT with colleagues — they drag and drop it the same way"
