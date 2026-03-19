@echo off
REM ============================================================================
REM Manual Python Dependencies Installation (For troubleshooting)
REM ============================================================================

echo.
echo ============================================================================
echo    Installing Python Dependencies Manually
echo ============================================================================
echo.

echo [INFO] Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH
    pause
    exit /b 1
)

echo.
echo [INFO] Installing core dependencies...
echo.

REM Install each package individually to catch specific errors
echo [1/10] Installing python-dotenv...
python -m pip install python-dotenv

echo [2/10] Installing google-generativeai...
python -m pip install google-generativeai

echo [3/10] Installing requests...
python -m pip install requests

echo [4/10] Installing beautifulsoup4...
python -m pip install beautifulsoup4

echo [5/10] Installing lxml...
python -m pip install lxml

echo [6/10] Installing fastapi...
python -m pip install fastapi

echo [7/10] Installing uvicorn...
python -m pip install uvicorn

echo [8/10] Installing pydantic...
python -m pip install pydantic

echo [9/10] Installing pandas...
python -m pip install pandas

echo [10/10] Installing additional dependencies...
python -m pip install numpy openpyxl python-multipart

echo.
echo ============================================================================
echo    Installation Complete!
echo ============================================================================
echo.
echo Run this to verify:
echo python -m pip list
echo.
pause
