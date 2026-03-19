@echo off
REM ============================================================================
REM Indian Tax Analysis System - Automated Setup Script (Windows)
REM ============================================================================

echo.
echo ============================================================================
echo    Indian Tax Analysis System - Automated Setup
echo ============================================================================
echo.

REM Check if git is installed
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed. Please install Git from https://git-scm.com/
    pause
    exit /b 1
)

REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check if Node.js is installed
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed. Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [INFO] All prerequisites found!
echo.

REM Clone or pull repository
if exist ".git" (
    echo [STEP 1/5] Pulling latest changes from GitHub...
    git pull origin main
) else (
    echo [STEP 1/5] Cloning repository from GitHub...
    cd ..
    git clone https://github.com/Pratham-Solanki911/TaxAnalyst.git
    cd TaxAnalyst
)

if %errorlevel% neq 0 (
    echo [ERROR] Failed to clone/pull repository
    pause
    exit /b 1
)

echo [SUCCESS] Repository updated!
echo.

REM Setup environment files
echo [STEP 2/5] Setting up environment files...

REM Backend .env
if not exist ".env" (
    echo [INFO] Creating backend .env file...
    (
        echo # Gemini API Configuration
        echo # Get your API key from: https://makersuite.google.com/app/apikey
        echo GEMINI_API_KEY=your-gemini-api-key-here
    ) > .env
    echo [WARN] Please update .env with your actual GEMINI_API_KEY
) else (
    echo [INFO] Backend .env already exists
)

REM Frontend .env
if not exist "frontend\.env" (
    echo [INFO] Creating frontend .env file...
    (
        echo # API Configuration
        echo VITE_API_URL=http://localhost:8000
        echo.
        echo # Google OAuth Configuration
        echo # Get your Client ID from: https://console.cloud.google.com/apis/credentials
        echo VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
    ) > frontend\.env
    echo [WARN] Please update frontend\.env with your VITE_GOOGLE_CLIENT_ID
    echo [INFO] Or use Development Mode to bypass Google OAuth
) else (
    echo [INFO] Frontend .env already exists
)

echo [SUCCESS] Environment files ready!
echo.

REM Install backend dependencies
echo [STEP 3/5] Installing Python dependencies...
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo [WARN] Pip upgrade failed, continuing...
)

echo [INFO] Installing requirements...
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies
    echo [INFO] This might be due to Python environment issues.
    echo [INFO] If you're using Anaconda, try: conda install --file requirements.txt
    echo [INFO] Or manually install: python -m pip install fastapi uvicorn pandas pydantic google-generativeai
    pause
    exit /b 1
)

echo [SUCCESS] Python dependencies installed!
echo.

REM Install frontend dependencies
echo [STEP 4/5] Installing Node.js dependencies...
cd frontend
call npm install

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Node.js dependencies
    cd ..
    pause
    exit /b 1
)

cd ..
echo [SUCCESS] Node.js dependencies installed!
echo.

REM Create start scripts
echo [STEP 5/5] Creating start scripts...

REM Create start-backend.bat
(
    echo @echo off
    echo echo Starting Backend Server...
    echo python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
) > start-backend.bat

REM Create start-frontend.bat
(
    echo @echo off
    echo echo Starting Frontend Server...
    echo cd frontend
    echo call npm run dev
) > start-frontend.bat

REM Create start-all.bat
(
    echo @echo off
    echo echo Starting Tax Analysis System...
    echo echo.
    echo echo Opening Backend in new window...
    echo start "Tax Analysis - Backend" cmd /k start-backend.bat
    echo timeout /t 3 /nobreak ^>nul
    echo echo Opening Frontend in new window...
    echo start "Tax Analysis - Frontend" cmd /k start-frontend.bat
    echo echo.
    echo echo ============================================================================
    echo echo    Tax Analysis System is starting!
    echo echo ============================================================================
    echo echo.
    echo echo Backend API: http://localhost:8000
    echo echo Frontend UI: http://localhost:3000
    echo echo.
    echo echo Press Ctrl+C in each window to stop the servers
    echo echo.
    echo timeout /t 5
) > start-all.bat

echo [SUCCESS] Start scripts created!
echo.

echo ============================================================================
echo    Setup Complete!
echo ============================================================================
echo.
echo IMPORTANT: Configure your environment variables:
echo.
echo 1. Edit .env and add your GEMINI_API_KEY
echo    Get it from: https://makersuite.google.com/app/apikey
echo.
echo 2. Edit frontend\.env and add your VITE_GOOGLE_CLIENT_ID
echo    Get it from: https://console.cloud.google.com/apis/credentials
echo    OR use "Continue as Developer" button to bypass Google OAuth
echo.
echo To start the application:
echo    - Run: start-all.bat (starts both backend and frontend)
echo    - Or run: start-backend.bat and start-frontend.bat separately
echo.
echo Access the application at: http://localhost:3000
echo.
echo ============================================================================

pause
