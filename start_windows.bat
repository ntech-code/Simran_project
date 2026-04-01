@echo off
echo =========================================================
echo   Indian Tax Analysis System - 1-Click Setup (Windows)
echo =========================================================
echo.

docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed!
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b
)

if not exist .env (
    echo [WARNING] .env file not found!
    echo Please create it using ENV_SETUP_GUIDE.md
    pause
)

echo [1/3] Stopping any old instances...
docker-compose down --remove-orphans >nul 2>&1

echo [2/3] Building and starting (first run takes a few minutes)...
docker-compose up -d --build

echo [3/3] Opening the application...
timeout /t 5
start http://localhost:3000

echo.
echo =========================================================
echo   DONE! Open http://localhost:3000 in your browser
echo   To stop: run 'docker-compose down'
echo =========================================================
pause
