#!/usr/bin/env bash
# new_project.sh — Bootstrap a new project from this FastAPI template.
#
# Usage:
#   bash scripts/new_project.sh
#   bash scripts/new_project.sh --name my-api --dest ../my-api

set -euo pipefail

# ── Parse arguments ───────────────────────────────────────────────────────────
PROJECT_NAME=""
DEST_DIR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --name) PROJECT_NAME="$2"; shift 2 ;;
        --dest) DEST_DIR="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

# Interactive prompts if args not provided
if [[ -z "$PROJECT_NAME" ]]; then
    read -rp "Project name (e.g. my-api): " PROJECT_NAME
fi
if [[ -z "$PROJECT_NAME" ]]; then
    echo "Error: project name cannot be empty." >&2; exit 1
fi

# Convert to safe identifiers
SNAKE_NAME="${PROJECT_NAME//-/_}"   # my-api → my_api (for Python module names)

if [[ -z "$DEST_DIR" ]]; then
    DEST_DIR="../${PROJECT_NAME}"
fi

# Resolve absolute path of the template dir (wherever this script lives)
TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo ""
echo "Creating new project:"
echo "  Name       : $PROJECT_NAME"
echo "  Identifier : $SNAKE_NAME"
echo "  Destination: $DEST_DIR"
echo ""

# ── Copy template ─────────────────────────────────────────────────────────────
if [[ -d "$DEST_DIR" ]]; then
    echo "Error: destination '$DEST_DIR' already exists." >&2; exit 1
fi

cp -r "$TEMPLATE_DIR" "$DEST_DIR"

# Remove git history so the new project starts fresh
rm -rf "$DEST_DIR/.git"

# ── Replace placeholder strings ───────────────────────────────────────────────
echo "Replacing placeholders..."

# Detect sed in-place flag (-i '' on macOS, -i on Linux)
if sed --version 2>/dev/null | grep -q GNU; then
    SED_INPLACE="sed -i"
else
    SED_INPLACE="sed -i ''"
fi

# Files to update
FILES_TO_UPDATE=(
    "$DEST_DIR/app/configs/config_handler.py"
    "$DEST_DIR/.env.example"
    "$DEST_DIR/.env"
    "$DEST_DIR/.env.development"
    "$DEST_DIR/.env.staging"
    "$DEST_DIR/.env.production"
    "$DEST_DIR/docker-compose.yml"
    "$DEST_DIR/Dockerfile"
    "$DEST_DIR/README.md"
)

for f in "${FILES_TO_UPDATE[@]}"; do
    [[ -f "$f" ]] || continue
    $SED_INPLACE "s/fastapi-template/${PROJECT_NAME}/g" "$f"
    $SED_INPLACE "s/fastapi_template/${SNAKE_NAME}/g" "$f"
    $SED_INPLACE "s/project_name/${SNAKE_NAME}/g" "$f"
    $SED_INPLACE "s/FastAPI Template/${PROJECT_NAME}/g" "$f"
done

# ── Setup .env ────────────────────────────────────────────────────────────────
if [[ ! -f "$DEST_DIR/.env" ]] && [[ -f "$DEST_DIR/.env.example" ]]; then
    cp "$DEST_DIR/.env.example" "$DEST_DIR/.env"
    echo "Created .env from .env.example"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "Done! Project created at: $DEST_DIR"
echo ""
echo "Next steps:"
echo "  cd $DEST_DIR"
echo "  # Edit .env with your database credentials"
echo "  pip install -r requirements.txt"
echo "  python -m app.main"
