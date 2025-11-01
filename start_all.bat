@echo off
echo ========================================
echo   LOCAL SCHEDULING AGENT STARTUP
echo ========================================
echo.

echo Step 1: Starting Ollama...
start "Ollama Server" ollama serve
timeout /t 3 /nobreak >nul

echo Step 2: Pulling Qwen 2.5 7B model...
ollama pull qwen2.5:7b

echo Step 3: Starting Backend...
start "Backend Server" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"

echo Step 4: Starting Frontend...
start "Frontend Server" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo   ALL SERVICES STARTED!
echo ========================================
echo.
echo Access your application at:
echo   Chat Interface: http://localhost:3000/chat
echo   Calendar View:  http://localhost:3000/calendar
echo   Backend API:    http://localhost:8000
echo   Health Check:   http://localhost:8000/health
echo.
echo Press any key to exit...
pause >nul