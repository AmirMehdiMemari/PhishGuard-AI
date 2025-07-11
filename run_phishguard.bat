@echo off
REM ─────────────────────────────────────────────────────────────
REM run_phishguard.bat
REM Batch launcher for PhishGuard AI (main.py)
REM ─────────────────────────────────────────────────────────────

REM 1) Move into this batch file’s directory
cd /d "%~dp0"

REM 2) (Optional) Activate Python virtual environment if you have one
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call "venv\Scripts\activate.bat"
)

REM 3) Run the main script
echo Launching PhishGuard AI…
python main.py %*

REM 4) Keep the window open so you can read any output/errors
pause
