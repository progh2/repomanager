@echo off
rem RepoManager launcher for Windows.
rem Creates .venv on first run, installs dependencies, then starts the app.
setlocal
cd /d "%~dp0"

set "VENV_PY=.venv\Scripts\python.exe"

where python >nul 2>nul
if errorlevel 1 (
    echo [RepoManager] Python not found. Install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

if not exist "%VENV_PY%" (
    echo [RepoManager] Creating virtual environment...
    python -m venv .venv || goto :fail
    echo [RepoManager] Installing dependencies...
    "%VENV_PY%" -m pip install --upgrade pip || goto :fail
    "%VENV_PY%" -m pip install -r requirements.txt || goto :fail
)

if "%~1"=="--update" (
    echo [RepoManager] Updating dependencies...
    "%VENV_PY%" -m pip install --upgrade -r requirements.txt || goto :fail
)

set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
"%VENV_PY%" -m repomanager
exit /b %errorlevel%

:fail
echo [RepoManager] Setup failed. See messages above.
pause
exit /b 1
