@echo off
echo Starting Backend Server...
cd /d %~dp0
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000