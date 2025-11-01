"""
Configuration settings for the scheduling agent
"""

# Ollama Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:7b"  # Optimal for RTX 3050
# DEFAULT_MODEL = "phi3:mini"  # Optimal for CPU
# DEFAULT_MODEL = "lamma:core"  # Optimal for RTX 3050
ALTERNATIVE_MODELS = ["llama3.2:8b", "qwen2.5:3b"]

# Model Parameters
MODEL_TEMPERATURE = 0.1
MODEL_TIMEOUT = 30

# API Configuration
API_HOST = "127.0.0.1"
API_PORT = 8000
CORS_ORIGINS = ["http://localhost:3000"]

# Data Configuration
TASKS_FILE_PATH = "data/tasks.json"