@echo off
setlocal

echo.
echo =========================================
echo    Harness Engineering - Setup
echo =========================================
echo.

:: Check Python
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo         Install from: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

:: Create virtualenv
echo [2/5] Creating virtual environment...
if not exist ".venv" (
    python -m venv .venv
    echo [OK] .venv created
) else (
    echo [OK] .venv already exists
)
call .venv\Scripts\activate.bat
echo.

:: Install packages
echo [3/5] Installing packages...
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
echo [OK] Packages installed
echo.

:: Create .env
echo [4/5] Setting up .env...
if not exist ".env" (
    copy .env.example .env >nul
    echo [OK] .env created from .env.example
    echo.
    echo  *** Open .env and fill in your keys ***
    echo  - ANTHROPIC_API_KEY  : https://console.anthropic.com
    echo  - GITHUB_TOKEN       : https://github.com/settings/tokens
    echo  - GITHUB_USERNAME    : your GitHub username
    echo  - DISCORD_WEBHOOK_URL: Discord server settings > Integrations > Webhooks
    echo.
) else (
    echo [OK] .env already exists
)
echo.

:: Check Ollama
echo [5/5] Checking Ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo [WARN] Ollama not found.
    echo        Install from: https://ollama.com
    echo        Then run: ollama pull gemma3:4b
) else (
    echo [OK] Ollama found
    ollama list 2>nul | findstr "gemma3" >nul
    if errorlevel 1 (
        echo [WARN] Gemma model not found. Run: ollama pull gemma3:4b
    ) else (
        echo [OK] Gemma model available
    )
)
echo.

echo =========================================
echo    Setup complete! Next steps:
echo =========================================
echo.
echo  1. Edit .env with your API keys:
echo     notepad .env
echo.
echo  2. Create GitHub repo:
echo     python scripts\create_github_repo.py
echo.
echo  3. Check system status:
echo     python main.py status
echo.
echo  NOTE: Activate venv in new sessions with:
echo        .venv\Scripts\activate
echo.
pause
