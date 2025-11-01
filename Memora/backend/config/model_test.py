"""
Model testing utilities for Ollama integration
"""

import requests
import json
from typing import Dict, Any, Optional
from langchain_ollama import OllamaLLM
from .settings import OLLAMA_BASE_URL, DEFAULT_MODEL, ALTERNATIVE_MODELS, MODEL_TEMPERATURE


def check_ollama_status() -> Dict[str, Any]:
    """Check if Ollama service is running"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return {
                "status": "running",
                "available_models": [model['name'] for model in models]
            }
        else:
            return {"status": "error", "message": "Ollama service not responding"}
    except requests.exceptions.RequestException as e:
        return {"status": "offline", "message": str(e)}


def test_model_performance(model_name: str = DEFAULT_MODEL) -> Dict[str, Any]:
    """Test Ollama model performance with sample scheduling task"""
    try:
        llm = OllamaLLM(
            model=model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=MODEL_TEMPERATURE
        )
        
        test_prompt = "Create a task: Meeting with client tomorrow at 3 PM"
        
        # Test basic response
        response = llm.invoke(test_prompt)
        
        return {
            "status": "success",
            "model": model_name,
            "test_prompt": test_prompt,
            "response": response,
            "response_length": len(response) if response else 0
        }
    
    except Exception as e:
        return {
            "status": "error",
            "model": model_name,
            "error": str(e)
        }


def test_all_models() -> Dict[str, Dict[str, Any]]:
    """Test all configured models"""
    results = {}
    
    # Check Ollama status first
    ollama_status = check_ollama_status()
    if ollama_status["status"] != "running":
        return {"ollama_status": ollama_status}
    
    # Test default model
    results[DEFAULT_MODEL] = test_model_performance(DEFAULT_MODEL)
    
    # Test alternative models if available
    available_models = ollama_status.get("available_models", [])
    for model in ALTERNATIVE_MODELS:
        if model in available_models:
            results[model] = test_model_performance(model)
        else:
            results[model] = {
                "status": "unavailable",
                "message": f"Model {model} not found in Ollama"
            }
    
    return results


def get_model_recommendations() -> Dict[str, str]:
    """Get model recommendations based on hardware"""
    return {
        "rtx_3050_8gb": "qwen2.5:7b (Recommended - 4.7GB VRAM)",
        "alternative_1": "llama3.2:8b (Good context handling - 4.9GB VRAM)",
        "fallback": "qwen2.5:3b (Lightweight - 1.9GB VRAM)",
        "note": "Recommendations based on RTX 3050 8GB VRAM capacity"
    }


if __name__ == "__main__":
    # Quick test when run directly
    print("Testing Ollama Integration...")
    print("=" * 50)
    
    # Check Ollama status
    status = check_ollama_status()
    print(f"Ollama Status: {status}")
    
    if status["status"] == "running":
        # Test default model
        result = test_model_performance()
        print(f"\nDefault Model Test ({DEFAULT_MODEL}):")
        print(f"Status: {result['status']}")
        if result["status"] == "success":
            print(f"Response: {result['response'][:100]}...")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    
    # Show recommendations
    print(f"\nModel Recommendations:")
    recommendations = get_model_recommendations()
    for key, value in recommendations.items():
        print(f"  {key}: {value}")