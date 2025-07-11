@echo off
REM ──────────────────────────────────────────────
REM PhishGuard AI Windows Installer Script
REM ──────────────────────────────────────────────

REM 1) Create virtual environment
python -m venv venv
IF ERRORLEVEL 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

REM 2) Activate the venv
call venv\Scripts\activate.bat
IF ERRORLEVEL 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

REM 3) Upgrade pip
echo Upgrading pip...
pip install --upgrade pip
IF ERRORLEVEL 1 (
    echo [ERROR] pip upgrade failed.
    pause
    exit /b 1
)

REM 4) Install dependencies
echo Installing required Python packages...
pip install numpy>=1.21.0 scikit-learn>=1.0 joblib>=1.1.0 xgboost>=1.6.0 PyQt5>=5.15.0 reportlab>=3.6.0 matplotlib>=3.4.0
IF ERRORLEVEL 1 (
    echo [ERROR] One or more packages failed to install.
    pause
    exit /b 1
)

echo.
echo ──────────────────────────────────────────────
echo ✅  Setup Complete!
echo.
echo To start using PhishGuard AI:
echo   1) Activate venv:    call venv\Scripts\activate.bat
echo   2) Run the app:      python main.py
echo.
pause
