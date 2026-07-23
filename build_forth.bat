@echo off
setlocal
cd /d "%~dp0.."
docker compose run --rm osdev python3 tools/forthc.py extension/example.fth build/forth-demo.elf
