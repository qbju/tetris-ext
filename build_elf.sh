#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
docker compose run --rm osdev make -C extension