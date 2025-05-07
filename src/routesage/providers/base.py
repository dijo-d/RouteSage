# routesage/providers/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class LLMProvider(ABC):
    """Base abstract class for LLM providers."""
    
    def __init__(self, api_key: str, model_name: str, timeout: float = 30.0, **kwargs):
        """
        Initialize the LLM provider.
        
        Args:
            api_key: API key for the provider
            model_name: Name of the model to use
            timeout: Request timeout in seconds
            **kwargs: Additional provider-specific parameters
        """
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        self.kwargs = kwargs
        
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                      temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate text based on the provided prompt."""
        pass
    
    @abstractmethod
    def get_models(self) -> List[str]:
        """Get a list of available models for this provider."""
        pass
    
    @classmethod
    @abstractmethod
    def get_provider_name(cls) -> str:
        """Get the name of this provider."""
        pass