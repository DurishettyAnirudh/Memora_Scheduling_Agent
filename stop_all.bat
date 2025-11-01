@echo off
echo ========================================
echo   STOPPING ALL SERVICES
echo ========================================
echo.

echo Stopping Backend Server (Python/Uvicorn)...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im uvicorn.exe >nul 2>&1

echo Stopping Frontend Server (Node/NPM)...
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im npm.exe >nul 2>&1

echo Stopping Ollama Server...
taskkill /f /im ollama.exe >nul 2>&1

echo.
echo ========================================
echo   ALL SERVICES STOPPED!
echo ========================================
echo.
echo All background processes have been terminated.
echo.
echo Press any key to exit...
pause >nul