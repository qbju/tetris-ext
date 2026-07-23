#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
docker compose run --rm osdev python3 tools/forthc.py extension/example.fth build/forth-demo.elf
