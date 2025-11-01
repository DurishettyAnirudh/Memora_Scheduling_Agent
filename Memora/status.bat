@echo off
echo ========================================
echo   SERVICE STATUS CHECK
echo ========================================
echo.

echo Checking Ollama Server...
tasklist /fi "imagename eq ollama.exe" | findstr ollama.exe >nul
if %errorlevel% == 0 (
    echo ✅ Ollama Server: RUNNING
) else (
    echo ❌ Ollama Server: NOT RUNNING
)

echo.
echo Checking Backend Server...
tasklist /fi "imagename eq python.exe" | findstr python.exe >nul
if %errorlevel% == 0 (
    echo ✅ Backend Server: RUNNING
) else (
    echo ❌ Backend Server: NOT RUNNING
)

echo.
echo Checking Frontend Server...
tasklist /fi "imagename eq node.exe" | findstr node.exe >nul
if %errorlevel% == 0 (
    echo ✅ Frontend Server: RUNNING
) else (
    echo ❌ Frontend Server: NOT RUNNING
)

echo.
echo ========================================
echo   SERVICE URLS
echo ========================================
echo.
echo Chat Interface: http://localhost:3000/chat
echo Calendar View:  http://localhost:3000/calendar  
echo Backend API:    http://localhost:8000
echo Health Check:   http://localhost:8000/health
echo.
echo Press any key to exit...
pause >nul