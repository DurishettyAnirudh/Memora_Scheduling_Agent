"""
Model management utilities for swapping and configuring models
"""

from typing import Optional, Dict, Any
from langchain_ollama import OllamaLLM
from .settings import OLLAMA_BASE_URL, DEFAULT_MODEL, ALTERNATIVE_MODELS, MODEL_TEMPERATURE


class ModelManager:
    """Manages LLM model instances and swapping"""
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.current_model = model_name
        self.llm_instance = None
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        """Initialize the LLM instance with current model"""
        try:
            self.llm_instance = OllamaLLM(
                model=self.current_model,
                base_url=OLLAMA_BASE_URL,
                temperature=MODEL_TEMPERATURE
            )
        except Exception as e:
            print(f"Error initializing model {self.current_model}: {e}")
            self.llm_instance = None
    
    def switch_model(self, model_name: str) -> Dict[str, Any]:
        """Switch to a different model"""
        if model_name not in [DEFAULT_MODEL] + ALTERNATIVE_MODELS:
            return {
                "success": False,
                "message": f"Model {model_name} not in configured models",
                "available_models": [DEFAULT_MODEL] + ALTERNATIVE_MODELS
            }
        
        try:
            # Test the new model first
            test_llm = OllamaLLM(
                model=model_name,
                base_url=OLLAMA_BASE_URL,
                temperature=MODEL_TEMPERATURE
            )
            
            # Quick test
            test_response = test_llm.invoke("Hello")
            
            # If successful, switch
            self.current_model = model_name
            self.llm_instance = test_llm
            
            return {
                "success": True,
                "message": f"Successfully switched to {model_name}",
                "previous_model": self.current_model,
                "test_response": test_response[:50] + "..." if len(test_response) > 50 else test_response
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to switch to {model_name}: {str(e)}"
            }
    
    def get_current_model(self) -> str:
        """Get the currently active model name"""
        return self.current_model
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model and available alternatives"""
        return {
            "current_model": self.current_model,
            "available_models": [DEFAULT_MODEL] + ALTERNATIVE_MODELS,
            "model_status": "active" if self.llm_instance else "inactive",
            "base_url": OLLAMA_BASE_URL,
            "temperature": MODEL_TEMPERATURE
        }
    
    def invoke(self, prompt: str) -> Optional[str]:
        """Invoke the current model with a prompt"""
        if not self.llm_instance:
            self._initialize_model()
        
        if not self.llm_instance:
            return None
        
        try:
            return self.llm_instance.invoke(prompt)
        except Exception as e:
            print(f"Error invoking model: {e}")
            return None
    
    def is_ready(self) -> bool:
        """Check if the model manager is ready to process requests"""
        return self.llm_instance is not None


# Global model manager instance
model_manager = ModelManager()


def get_model_manager() -> ModelManager:
    """Get the global model manager instance"""
    return model_manager