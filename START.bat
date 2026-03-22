@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Indian Tax Analysis System - Docker Setup
color 0A

echo.
echo ========================================================================
echo        Indian Tax Analysis System - Docker Setup
echo ========================================================================
echo.
echo   PREREQUISITES: You need Docker Desktop installed.
echo   Download from: https://www.docker.com/products/docker-desktop/
echo.
echo ========================================================================
echo.

:: ============================================================================
:: STEP 1: Check Docker
:: ============================================================================
echo [STEP 1/4] Checking Docker...
echo.

where docker >nul 2>&1
if !errorlevel! neq 0 (
    echo   [ERROR] Docker is NOT installed!
    echo.
    echo   Please install Docker Desktop from:
    echo   https://www.docker.com/products/docker-desktop/
    echo.
    echo   After installing:
    echo     1. Open Docker Desktop
    echo     2. Wait until it says "Docker is running"
    echo     3. Run this script again
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

docker info >nul 2>&1
if !errorlevel! neq 0 (
    echo   [ERROR] Docker is installed but NOT running!
    echo.
    echo   Please open Docker Desktop and wait until it says "Running"
    echo   Then run this script again.
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo   [OK] Docker is installed and running!
echo.

:: ============================================================================
:: STEP 2: Clone the project (if not already)
:: ============================================================================
echo [STEP 2/4] Setting up project files...
echo.

set "REPO_URL=https://github.com/ntech-code/Tax-simran.git"
set "PROJECT_NAME=Tax-simran"
set "INSTALL_DIR=%USERPROFILE%\Desktop\%PROJECT_NAME%"

:: Check if already inside the project
if exist "docker-compose.yml" (
    if exist "api\main.py" (
        echo   [OK] Already inside the project folder.
        goto :PROJECT_READY
    )
)

:: Check if project exists on Desktop
if exist "!INSTALL_DIR!\docker-compose.yml" (
    echo   [OK] Project found at: !INSTALL_DIR!
    cd /d "!INSTALL_DIR!"
    goto :PROJECT_READY
)

:: Clone
echo   [INFO] Cloning project to Desktop...

where git >nul 2>&1
if !errorlevel! neq 0 (
    echo   [ERROR] Git is NOT installed!
    echo   Install from: https://git-scm.com/downloads
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

cd /d "%USERPROFILE%\Desktop"
git clone %REPO_URL% 2>&1
if !errorlevel! neq 0 (
    echo   [ERROR] Failed to clone. Check internet connection.
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

cd /d "!INSTALL_DIR!"
echo   [OK] Project cloned!

:PROJECT_READY
echo.

:: ============================================================================
:: STEP 3: Get API Key
:: ============================================================================
echo [STEP 3/4] Setting up API Key...
echo.

set "NEED_KEY=1"
if exist ".env" (
    findstr /C:"GEMINI_API_KEY=" .env >nul 2>&1
    if !errorlevel! equ 0 (
        findstr /C:"your-gemini-api-key-here" .env >nul 2>&1
        if !errorlevel! neq 0 (
            echo   [OK] API key already configured.
            set /p "CHANGE_KEY=  Change it? (y/N): "
            if /i "!CHANGE_KEY!" neq "y" set "NEED_KEY=0"
        )
    )
)

if "!NEED_KEY!"=="1" (
    echo.
    echo   You need a FREE Gemini API Key:
    echo     1. Go to: https://makersuite.google.com/app/apikey
    echo     2. Click "Create API Key"
    echo     3. Paste it below
    echo.
    set /p "API_KEY=  Your Gemini API Key: "
    if "!API_KEY!"=="" (
        echo   [ERROR] Key cannot be empty!
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    echo GEMINI_API_KEY=!API_KEY!> .env
    echo   [OK] API key saved!
)
echo.

:: ============================================================================
:: STEP 4: Build and Start with Docker
:: ============================================================================
echo [STEP 4/4] Building and starting with Docker...
echo.
echo   This will take 2-5 minutes on first run (downloading images).
echo   Subsequent runs will be much faster.
echo.

:: Stop any existing containers
docker compose down >nul 2>&1

:: Build and start
docker compose up --build -d
if !errorlevel! neq 0 (
    echo.
    echo   [ERROR] Docker build failed!
    echo   Check the error messages above.
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:: Wait for containers to be ready
echo.
echo   [INFO] Waiting for services to start...
timeout /t 5 /nobreak >nul

:: Check if containers are running
docker ps --filter "name=tax-backend" --filter "status=running" | findstr "tax-backend" >nul 2>&1
if !errorlevel! neq 0 (
    echo   [WARN] Backend may still be starting. Waiting a bit more...
    timeout /t 10 /nobreak >nul
)

:: Open browser
start "" http://localhost:3000

echo.
echo ========================================================================
echo.
echo        SUCCESS! The application is running!
echo.
echo ========================================================================
echo.
echo   Frontend:   http://localhost:3000
echo   Backend:    http://localhost:8000
echo   API Docs:   http://localhost:8000/docs
echo.
echo   LOGIN: Click "Continue as Developer" to skip Google login
echo.
echo   USEFUL COMMANDS:
echo     docker compose logs -f       = See live logs
echo     docker compose down          = Stop the app
echo     docker compose up -d         = Start the app again
echo.
echo ========================================================================
echo.
echo Press any key to close this window...
echo (The app keeps running in Docker)
pause >nul
