from typing import Optional, List
import openai
from .base import LLMProvider

class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""
    
    default_model = "gpt-3.5-turbo"
    supported_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"]

    def __init__(self, api_key: str, model_name: str = None, timeout: float = 30.0, **kwargs):
        super().__init__(api_key, model_name or self.default_model, timeout=timeout, **kwargs)
        if self.model_name not in self.supported_models:
            raise ValueError(f"Unsupported model: {self.model_name}. Supported models: {', '.join(self.supported_models)}")
        
        openai.api_key = api_key
        self.client = openai.AsyncOpenAI(timeout=timeout)

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                      temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate text using OpenAI model."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    def get_models(self) -> List[str]:
        """Get list of supported models."""
        return self.supported_models

    @classmethod
    def get_provider_name(cls) -> str:
        """Get provider name."""
        return "openai"