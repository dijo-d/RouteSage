from typing import Optional, List, ClassVar
import aiohttp
from .base import LLMProvider

class DeepSeekProvider(LLMProvider):
    """DeepSeek API provider."""
    
    default_model: ClassVar[str] = "deepseek-chat"
    supported_models: ClassVar[List[str]] = ["deepseek-chat", "deepseek-coder"]
    API_URL: ClassVar[str] = "https://api.deepseek.com/v1/chat/completions"

    def __init__(self, api_key: str, model_name: str = None, **kwargs):
        super().__init__(api_key, model_name or self.default_model, **kwargs)
        if self.model_name not in self.supported_models:
            raise ValueError(f"Unsupported model: {self.model_name}. Supported models: {', '.join(self.supported_models)}")
        
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                      temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate text using DeepSeek model."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.API_URL, 
                    json=payload, 
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API returned {response.status}: {error_text}")
                    
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
            
        except Exception as e:
            raise Exception(f"DeepSeek API error: {str(e)}")

    def get_models(self) -> List[str]:
        """Get list of supported models."""
        return self.supported_models

    @classmethod
    def get_provider_name(cls) -> str:
        """Get provider name."""
        return "deepseek"