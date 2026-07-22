@echo off
setlocal
cd /d "%~dp0.."
docker compose run --rm osdev make -C extension
if errorlevel 1 exit /b %errorlevel%