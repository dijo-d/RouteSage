from typing import Optional, List
import json
import re  # Add this import
import google.generativeai as genai
from ..utils.logger import get_logger
from .base import LLMProvider

# Initialize logger
logger = get_logger()

class GeminiProvider(LLMProvider):
    """Google's Gemini API provider."""
    
    default_model = "gemini-pro"
    supported_models = ["gemini-pro", "gemini-2.0-flash"]

    def __init__(self, api_key: str, model_name: str = None, **kwargs):
        """Initialize Gemini provider."""
        super().__init__(api_key, model_name, **kwargs)
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name or self.default_model)

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                  temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate text using Gemini model."""
        try:
            # Format the prompt to ensure proper analysis
            formatted_prompt = f"""Analyze this FastAPI code and provide documentation in JSON format.
For each endpoint, include:
1. Path and HTTP methods
2. A clear, detailed description of what the endpoint does
3. Parameters and their descriptions
4. Response details
5. Appropriate tags for grouping

System Context:
{system_prompt if system_prompt else ''}

Code to Analyze:
{prompt}

Remember to maintain valid JSON format in your response."""

            response = await self.model.generate_content_async(
                formatted_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens * 2  # Increase token limit
                )
            )
            
            if not response or not response.text:
                raise Exception("Empty response from Gemini API")
            
            # Clean and validate the response
            cleaned_response = response.text.strip()
            
            # Handle potential multi-part responses
            if isinstance(cleaned_response, list):
                cleaned_response = ''.join(cleaned_response)
            
            # Remove any markdown code block markers
            cleaned_response = re.sub(r'```json\s*|\s*```', '', cleaned_response)
            cleaned_response = cleaned_response.strip()
            
            # Try to fix common JSON issues
            cleaned_response = cleaned_response.replace('\n', ' ')
            cleaned_response = re.sub(r'\s+', ' ', cleaned_response)
            
            # Validate JSON
            try:
                parsed_json = json.loads(cleaned_response)
                # Ensure the response is properly formatted
                return json.dumps(parsed_json, indent=2)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from Gemini: {cleaned_response}")
                # Try to fix truncated JSON
                if '"routes": [' in cleaned_response:
                    try:
                        # Extract the valid part and close the JSON structure
                        valid_part = cleaned_response[:cleaned_response.rindex('}') + 1]
                        valid_part += ']}'
                        json.loads(valid_part)  # Validate the fixed JSON
                        return valid_part
                    except (json.JSONDecodeError, ValueError):
                        pass
                raise Exception(f"Invalid JSON response: {str(e)}")
                
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise

    def get_models(self) -> List[str]:
        """Get list of supported models."""
        return self.supported_models

    @classmethod
    def get_provider_name(cls) -> str:
        """Get provider name."""
        return "gemini"