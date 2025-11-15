#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR" || exit 1

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker no está instalado o en PATH" >&2
  exit 1
fi

echo "Construyendo y levantando perfiles core+app..."
docker compose -f infra/docker/docker-compose.yml --profile core --profile app up -d --build

echo "Servicios levantados. Web: http://localhost:3000, Gateway: http://localhost:8088"
