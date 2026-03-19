@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Indian Tax Analysis System - Complete Setup
color 0A

echo.
echo ========================================================================
echo        Indian Tax Analysis System - Complete Auto Setup
echo ========================================================================
echo.
echo   This script will:
echo     1. Check if Python, Node.js, Git are installed
echo     2. Clone the project from GitHub
echo     3. Ask you for your Gemini API Key
echo     4. Install all dependencies
echo     5. Clear any blocked ports
echo     6. Start the application
echo     7. Open it in your browser
echo.
echo ========================================================================
echo.
pause

:: ============================================================================
:: STEP 1: Check Prerequisites
:: ============================================================================
echo.
echo [STEP 1/7] Checking prerequisites...
echo -----------------------------------------------

:: ---------- Check Python ----------
set "PYTHON_CMD="
where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    set "PIP_CMD=pip"
) else (
    where python3 >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=python3"
        set "PIP_CMD=pip3"
    )
)

if "!PYTHON_CMD!"=="" (
    echo.
    echo [ERROR] Python is NOT installed!
    echo.
    echo   Please download and install Python 3.8+ from:
    echo   https://www.python.org/downloads/
    echo.
    echo   IMPORTANT: During installation, CHECK the box that says
    echo   "Add Python to PATH" at the bottom of the installer!
    echo.
    echo   After installing, CLOSE this window and run this script again.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('!PYTHON_CMD! --version 2^>^&1') do echo   [OK] %%v found

:: ---------- Check Node.js ----------
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Node.js is NOT installed!
    echo.
    echo   Please download and install Node.js from:
    echo   https://nodejs.org/
    echo   (Download the LTS version)
    echo.
    echo   After installing, CLOSE this window and run this script again.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo   [OK] Node.js %%v found

:: ---------- Check npm ----------
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] npm is NOT found! It should come with Node.js.
    echo   Try reinstalling Node.js from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('npm --version 2^>^&1') do echo   [OK] npm %%v found

:: ---------- Check Git ----------
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Git is NOT installed!
    echo.
    echo   Please download and install Git from:
    echo   https://git-scm.com/downloads
    echo.
    echo   After installing, CLOSE this window and run this script again.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('git --version 2^>^&1') do echo   [OK] %%v found

echo.
echo   All prerequisites are installed!
echo.

:: ============================================================================
:: STEP 2: Clone the Project
:: ============================================================================
echo [STEP 2/7] Setting up project...
echo -----------------------------------------------

set "REPO_URL=https://github.com/ntech-code/Tax-simran.git"
set "PROJECT_NAME=Tax-simran"

:: Determine where to put the project (Desktop)
set "INSTALL_DIR=%USERPROFILE%\Desktop\%PROJECT_NAME%"

:: Check if already inside the project
if exist "api\main.py" if exist "frontend\package.json" (
    echo   [INFO] Already inside the project folder.
    echo   [INFO] Pulling latest changes...
    git pull origin main >nul 2>&1 || git pull origin master >nul 2>&1
    echo   [OK] Project is up to date.
    goto :PROJECT_READY
)

:: Check if project already exists on Desktop
if exist "!INSTALL_DIR!\api\main.py" (
    echo   [INFO] Project already exists at: !INSTALL_DIR!
    echo   [INFO] Pulling latest changes...
    cd /d "!INSTALL_DIR!"
    git pull origin main >nul 2>&1 || git pull origin master >nul 2>&1
    echo   [OK] Project updated.
    goto :PROJECT_READY
)

:: Clone fresh
echo   [INFO] Cloning project to your Desktop...
echo   Location: !INSTALL_DIR!
echo.

cd /d "%USERPROFILE%\Desktop"
git clone %REPO_URL% 2>&1

if %errorlevel% neq 0 (
    echo.
    echo   [ERROR] Failed to clone! Check your internet connection.
    echo   Make sure you can access: %REPO_URL%
    echo.
    pause
    exit /b 1
)

cd /d "!INSTALL_DIR!"
echo   [OK] Project cloned successfully!

:PROJECT_READY
echo.

:: ============================================================================
:: STEP 3: Get Gemini API Key
:: ============================================================================
echo [STEP 3/7] Setting up API Key...
echo -----------------------------------------------

:: Check if .env already has a valid key
set "NEED_KEY=1"
if exist ".env" (
    findstr /C:"your-gemini-api-key-here" .env >nul 2>&1
    if %errorlevel% neq 0 (
        :: Has a non-placeholder key
        for /f "tokens=2 delims==" %%k in ('findstr /C:"GEMINI_API_KEY" .env 2^>nul') do (
            if not "%%k"=="" (
                echo   [INFO] API key already configured.
                set /p "CHANGE_KEY=  Do you want to change it? (y/N): "
                if /i "!CHANGE_KEY!" neq "y" (
                    set "NEED_KEY=0"
                )
            )
        )
    )
)

if "!NEED_KEY!"=="1" (
    echo.
    echo   ================================================================
    echo   You need a FREE Gemini API Key for the AI features.
    echo.
    echo   How to get it:
    echo     1. Open this link in your browser:
    echo        https://makersuite.google.com/app/apikey
    echo     2. Sign in with your Google account
    echo     3. Click "Create API Key"
    echo     4. Copy the key and paste it below
    echo   ================================================================
    echo.
    set /p "API_KEY=  Paste your Gemini API Key here: "
    
    if "!API_KEY!"=="" (
        echo.
        echo   [ERROR] API key cannot be empty!
        pause
        exit /b 1
    )
    
    :: Save to .env
    echo GEMINI_API_KEY=!API_KEY!> .env
    echo   [OK] API key saved!
)

echo.

:: ============================================================================
:: STEP 4: Setup Frontend Config
:: ============================================================================
echo [STEP 4/7] Configuring frontend...
echo -----------------------------------------------

if not exist "frontend\.env" (
    (
        echo VITE_API_URL=http://localhost:8000
        echo VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
    ) > "frontend\.env"
    echo   [OK] Frontend config created.
) else (
    echo   [OK] Frontend config already exists.
)

echo   [TIP] Use "Continue as Developer" button to skip Google login.
echo.

:: ============================================================================
:: STEP 5: Install Dependencies
:: ============================================================================
echo [STEP 5/7] Installing dependencies...
echo -----------------------------------------------
echo   This may take 2-5 minutes. Please wait...
echo.

:: Upgrade pip silently
!PYTHON_CMD! -m pip install --upgrade pip >nul 2>&1

:: Install Python dependencies
echo   [INFO] Installing Python packages...
!PIP_CMD! install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo   [WARN] Retrying with alternative method...
    !PYTHON_CMD! -m pip install -r requirements.txt
)
echo   [OK] Python packages installed!
echo.

:: Install Node.js dependencies
echo   [INFO] Installing Node.js packages (frontend)...
cd frontend
call npm install >nul 2>&1
if %errorlevel% neq 0 (
    echo   [WARN] Cleaning and retrying...
    rd /s /q node_modules 2>nul
    del package-lock.json 2>nul
    call npm install
)
cd ..
echo   [OK] Node.js packages installed!
echo.

:: ============================================================================
:: STEP 6: Clear Ports
:: ============================================================================
echo [STEP 6/7] Clearing ports 8000 and 3000...
echo -----------------------------------------------

:: Kill anything on port 8000
set "KILLED_8000=0"
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    if "%%a" neq "0" (
        taskkill /F /PID %%a >nul 2>&1
        set "KILLED_8000=1"
    )
)
if "!KILLED_8000!"=="1" (
    echo   [OK] Cleared port 8000
) else (
    echo   [OK] Port 8000 is free
)

:: Kill anything on port 3000
set "KILLED_3000=0"
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":3000 " ^| findstr "LISTENING"') do (
    if "%%a" neq "0" (
        taskkill /F /PID %%a >nul 2>&1
        set "KILLED_3000=1"
    )
)
if "!KILLED_3000!"=="1" (
    echo   [OK] Cleared port 3000
) else (
    echo   [OK] Port 3000 is free
)

echo.

:: ============================================================================
:: STEP 7: Start the Application
:: ============================================================================
echo [STEP 7/7] Starting the application...
echo -----------------------------------------------
echo.

:: Get current directory for absolute paths
set "PROJECT_PATH=%cd%"

:: Start backend server in a new window
echo   [INFO] Starting Backend API (port 8000)...
start "Tax System - Backend API" cmd /k "cd /d "!PROJECT_PATH!" && !PYTHON_CMD! -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"

:: Wait for backend to initialize
echo   [INFO] Waiting for backend to start...
timeout /t 6 /nobreak >nul

:: Start frontend server in a new window
echo   [INFO] Starting Frontend (port 3000)...
start "Tax System - Frontend" cmd /k "cd /d "!PROJECT_PATH!\frontend" && npm run dev"

:: Wait for frontend to initialize
echo   [INFO] Waiting for frontend to start...
timeout /t 6 /nobreak >nul

:: Open in default browser
echo   [INFO] Opening in your browser...
start "" http://localhost:3000

:: ============================================================================
:: SUCCESS
:: ============================================================================
echo.
echo ========================================================================
echo.
echo        Setup Complete! The application is running!
echo.
echo ========================================================================
echo.
echo   Frontend App:  http://localhost:3000
echo   Backend API:   http://localhost:8000
echo   API Docs:      http://localhost:8000/docs
echo.
echo   LOGIN: Click "Continue as Developer" on the login page
echo         to start using the app immediately!
echo.
echo   TO STOP: Close the "Backend API" and "Frontend" windows
echo.
echo   TO RUN AGAIN: Just double-click this script!
echo.
echo ========================================================================
echo.
echo Press any key to close this setup window...
echo (The app will keep running in the other windows)
pause >nul
