@echo off
echo Starting Ollama Integration Test...
echo ====================================

echo.
echo Step 1: Checking if Ollama is running...
python -c "from config.model_test import check_ollama_status; status = check_ollama_status(); print(f'Status: {status[\"status\"]}'); print(f'Message: {status.get(\"message\", \"N/A\")}') if status['status'] != 'running' else print(f'Available models: {status.get(\"available_models\", [])}')"

echo.
echo Step 2: Model Recommendations for RTX 3050 8GB:
python -c "from config.model_test import get_model_recommendations; recs = get_model_recommendations(); [print(f'  {k}: {v}') for k, v in recs.items()]"

echo.
echo Step 3: Model Manager Status:
python -c "from config.model_manager import ModelManager; mm = ModelManager(); info = mm.get_model_info(); print(f'Current Model: {info[\"current_model\"]}'); print(f'Status: {info[\"model_status\"]}'); print(f'Available Models: {info[\"available_models\"]}')"

echo.
echo ====================================
echo If Ollama is offline, start it with:
echo   ollama serve
echo Then pull the recommended model:
echo   ollama pull qwen2.5:7b
echo ====================================
pause