@echo off
setlocal

cd /d %~dp0\..

set PYTHON_CMD=python
if exist .venv\Scripts\python.exe (
    set PYTHON_CMD=.venv\Scripts\python.exe
)

echo [0/3] Stopping running app process...
taskkill /f /im DataAnalysisApp.exe >nul 2>nul

echo [1/3] Cleaning old build artifacts...
call scripts\clean.bat
if errorlevel 1 exit /b 1

echo [2/3] Running PyInstaller build...
%PYTHON_CMD% -m PyInstaller --noconfirm --clean DataAnalysisApp.spec
if errorlevel 1 (
    echo Build failed.
    exit /b 1
)

echo [3/3] Build completed.
echo Output: dist\DataAnalysisApp\DataAnalysisApp.exe
exit /b 0
