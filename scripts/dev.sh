#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
cp -n .env.example .env || true
echo "Starting Postgres/Redis via docker compose (if available)..."
docker compose up -d db redis 2>/dev/null || true
echo "Backend: http://localhost:8000  Frontend: http://localhost:3000"
echo "See docs/INSTALLATION.md for full instructions."
