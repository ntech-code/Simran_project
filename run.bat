@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Indian Tax Analysis System - One Click Setup
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║       🇮🇳  Indian Tax Analysis System - One Click Setup  🇮🇳      ║
echo ╠══════════════════════════════════════════════════════════════════╣
echo ║  This script will set up everything automatically.             ║
echo ║  Just sit back and relax!                                      ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

:: ============================================================================
:: STEP 1: Check Prerequisites
:: ============================================================================
echo [STEP 1/7] Checking prerequisites...
echo.

:: Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    where python3 >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python is NOT installed!
        echo.
        echo Please install Python 3.8+ from: https://www.python.org/downloads/
        echo IMPORTANT: Check "Add Python to PATH" during installation!
        echo.
        echo After installing Python, run this script again.
        pause
        exit /b 1
    ) else (
        set "PYTHON_CMD=python3"
        set "PIP_CMD=pip3"
    )
) else (
    set "PYTHON_CMD=python"
    set "PIP_CMD=pip"
)

:: Verify Python version
%PYTHON_CMD% --version 2>&1
echo [OK] Python found!

:: Check Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is NOT installed!
    echo.
    echo Please install Node.js 16+ from: https://nodejs.org/
    echo Download the LTS version and install it.
    echo.
    echo After installing Node.js, run this script again.
    pause
    exit /b 1
)

node --version 2>&1
echo [OK] Node.js found!

:: Check Git
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is NOT installed!
    echo.
    echo Please install Git from: https://git-scm.com/downloads
    echo.
    echo After installing Git, run this script again.
    pause
    exit /b 1
)

git --version 2>&1
echo [OK] Git found!
echo.
echo [SUCCESS] All prerequisites are installed!
echo.

:: ============================================================================
:: STEP 2: Clone or Update Repository
:: ============================================================================
echo [STEP 2/7] Setting up project files...
echo.

set "REPO_URL=https://github.com/ntech-code/Tax-simran.git"
set "PROJECT_DIR=Tax-simran"

:: Check if we're already inside the project directory
if exist "api\main.py" (
    echo [INFO] Already inside the project directory. Pulling latest changes...
    git pull origin main 2>nul || git pull origin master 2>nul || echo [WARN] Could not pull latest changes, continuing with existing files...
    goto :SKIP_CLONE
)

:: Check if project folder exists nearby
if exist "%PROJECT_DIR%" (
    echo [INFO] Project folder found. Pulling latest changes...
    cd "%PROJECT_DIR%"
    git pull origin main 2>nul || git pull origin master 2>nul || echo [WARN] Could not pull latest changes, continuing with existing files...
) else (
    echo [INFO] Cloning repository from GitHub...
    git clone %REPO_URL%
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to clone repository!
        echo Make sure you have internet access and the repo URL is correct.
        pause
        exit /b 1
    )
    cd "%PROJECT_DIR%"
)

:SKIP_CLONE
echo [SUCCESS] Project files ready!
echo.

:: ============================================================================
:: STEP 3: Get Gemini API Key
:: ============================================================================
echo [STEP 3/7] Configuring API Key...
echo.

if exist ".env" (
    findstr /C:"GEMINI_API_KEY=" .env >nul 2>&1
    if %errorlevel% equ 0 (
        :: Check if it's not the placeholder
        findstr /C:"your-gemini-api-key-here" .env >nul 2>&1
        if %errorlevel% neq 0 (
            echo [INFO] API key already configured in .env file.
            set /p "CHANGE_KEY=Do you want to change it? (y/N): "
            if /i "!CHANGE_KEY!" neq "y" goto :SKIP_API_KEY
        )
    )
)

echo ╔══════════════════════════════════════════════════════════════════╗
echo ║  You need a Gemini API Key to use AI features.                 ║
echo ║                                                                ║
echo ║  Get your FREE key from:                                       ║
echo ║  https://makersuite.google.com/app/apikey                      ║
echo ║                                                                ║
echo ║  1. Visit the link above                                       ║
echo ║  2. Click "Create API Key"                                     ║
echo ║  3. Copy and paste it below                                    ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.
set /p "API_KEY=Enter your Gemini API Key: "

if "!API_KEY!"=="" (
    echo [ERROR] API key cannot be empty!
    echo Please get your key from: https://makersuite.google.com/app/apikey
    pause
    exit /b 1
)

:: Create backend .env file
echo GEMINI_API_KEY=!API_KEY!> .env
echo [SUCCESS] API key saved!

:SKIP_API_KEY
echo.

:: ============================================================================
:: STEP 4: Setup Frontend Environment
:: ============================================================================
echo [STEP 4/7] Setting up frontend configuration...
echo.

if not exist "frontend\.env" (
    echo VITE_API_URL=http://localhost:8000> "frontend\.env"
    echo VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com>> "frontend\.env"
    echo [INFO] Frontend environment created.
    echo [TIP] You can use "Continue as Developer" mode to skip Google login.
) else (
    echo [INFO] Frontend .env already exists.
)

echo [SUCCESS] Frontend configured!
echo.

:: ============================================================================
:: STEP 5: Install Dependencies
:: ============================================================================
echo [STEP 5/7] Installing dependencies (this may take a few minutes)...
echo.

:: Upgrade pip
echo [INFO] Upgrading pip...
%PYTHON_CMD% -m pip install --upgrade pip >nul 2>&1

:: Install Python dependencies
echo [INFO] Installing Python packages...
%PIP_CMD% install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARN] Some Python packages may have had issues. Trying alternative install...
    %PYTHON_CMD% -m pip install -r requirements.txt
)
echo [SUCCESS] Python dependencies installed!
echo.

:: Install Node.js dependencies
echo [INFO] Installing Node.js packages...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo [WARN] npm install had issues. Cleaning and retrying...
    rmdir /s /q node_modules 2>nul
    del package-lock.json 2>nul
    call npm install
)
cd ..
echo [SUCCESS] Node.js dependencies installed!
echo.

:: ============================================================================
:: STEP 6: Clear Ports (Kill any existing processes)
:: ============================================================================
echo [STEP 6/7] Clearing ports 8000 and 3000...
echo.

:: Kill anything on port 8000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 " ^| findstr "LISTENING" 2^>nul') do (
    echo [INFO] Killing process on port 8000 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)

:: Kill anything on port 3000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000 " ^| findstr "LISTENING" 2^>nul') do (
    echo [INFO] Killing process on port 3000 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)

echo [SUCCESS] Ports cleared!
echo.

:: ============================================================================
:: STEP 7: Start Application
:: ============================================================================
echo [STEP 7/7] Starting the application...
echo.

:: Start backend in a new window
echo [INFO] Starting Backend API server (port 8000)...
start "Tax API - Backend" cmd /k "%PYTHON_CMD% -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"

:: Wait for backend to start
echo [INFO] Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

:: Start frontend in a new window
echo [INFO] Starting Frontend server (port 3000)...
start "Tax App - Frontend" cmd /k "cd frontend && npm run dev"

:: Wait for frontend to start
echo [INFO] Waiting for frontend to initialize...
timeout /t 5 /nobreak >nul

:: Open browser
echo [INFO] Opening application in browser...
timeout /t 3 /nobreak >nul
start http://localhost:3000

:: ============================================================================
:: Done!
:: ============================================================================
echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║                                                                ║
echo ║           ✅  Setup Complete! Everything is running!  ✅        ║
echo ║                                                                ║
echo ╠══════════════════════════════════════════════════════════════════╣
echo ║                                                                ║
echo ║   Frontend:  http://localhost:3000                             ║
echo ║   Backend:   http://localhost:8000                             ║
echo ║   API Docs:  http://localhost:8000/docs                        ║
echo ║                                                                ║
echo ║   LOGIN TIP: Click "Continue as Developer" to skip Google      ║
echo ║              OAuth setup and start using immediately!          ║
echo ║                                                                ║
echo ║   To stop: Close the Backend and Frontend terminal windows     ║
echo ║                                                                ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.
echo Press any key to exit this setup window (servers keep running)...
pause >nul
