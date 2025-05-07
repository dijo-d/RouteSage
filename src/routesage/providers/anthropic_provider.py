from typing import Optional, List
import anthropic
from .base import LLMProvider

class AnthropicProvider(LLMProvider):
    """Anthropic API provider."""
    
    default_model = "claude-3-opus"
    supported_models = ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]

    def __init__(self, api_key: str, model_name: str = None, timeout: float = 30.0, **kwargs):
        super().__init__(api_key, model_name or self.default_model, timeout=timeout, **kwargs)
        if self.model_name not in self.supported_models:
            raise ValueError(f"Unsupported model: {self.model_name}. Supported models: {', '.join(self.supported_models)}")
        
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key,
            timeout=timeout
        )

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                      temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate text using Anthropic model."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.messages.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.content[0].text
            
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

    def get_models(self) -> List[str]:
        """Get list of supported models."""
        return self.supported_models

    @classmethod
    def get_provider_name(cls) -> str:
        """Get provider name."""
        return "anthropic"