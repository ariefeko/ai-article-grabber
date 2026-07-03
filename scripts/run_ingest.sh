#!/usr/bin/env bash

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_DIR"

mkdir -p logs
mkdir -p data/articles

source .venv/bin/activate

python -m src.main >> logs/ingest.log 2>&1
