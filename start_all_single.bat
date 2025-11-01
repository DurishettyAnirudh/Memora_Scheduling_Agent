@echo off
echo ========================================
echo   LOCAL SCHEDULING AGENT STARTUP
echo ========================================
echo.

echo Step 1: Starting Ollama...
start /B ollama serve
timeout /t 3 /nobreak >nul

echo Step 2: Pulling Qwen 2.5 7B model...
ollama pull qwen2.5:7b

echo Step 3: Starting Backend...
cd /d "%~dp0backend"
start /B python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

echo Step 4: Starting Frontend...  
cd /d "%~dp0frontend"
start /B npm run dev

cd /d "%~dp0"

echo.
echo ========================================
echo   ALL SERVICES STARTED!
echo ========================================
echo.
echo All services are running in the background.
echo.
echo Access your application at:
echo   Chat Interface: http://localhost:3000/chat
echo   Calendar View:  http://localhost:3000/calendar
echo   Backend API:    http://localhost:8000
echo   Health Check:   http://localhost:8000
echo.
echo To stop all services, run: stop_all.bat
echo To see service status, run: status.bat
echo.
echo This terminal will remain open to show the status.
echo Press Ctrl+C to stop all services, or close this window.
echo.
pause