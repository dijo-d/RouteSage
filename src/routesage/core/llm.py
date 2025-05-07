from typing import Optional, Dict, Any
import asyncio
import json
from ..providers import get_provider
from .cache import LLMCache
from .models import APIDocumentation, RouteInfo, RouteParameter  # Added RouteParameter import
from .rate_limiter import RateLimiter
from ..utils.logger import get_logger

# Initialize logger
logger = get_logger()

async def enhance_documentation_with_llm(
    docs: APIDocumentation,
    provider_name: str,
    model_name: str,  # Made required by removing Optional
    api_key: str,
    cache_enabled: bool = True,
    temperature: float = 0.7,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> APIDocumentation:
    """
    Enhance API documentation using LLM.
    
    Args:
        docs: Original API documentation
        provider_name: Name of the LLM provider
        model_name: Model name to use (required)
        api_key: API key for the provider
        cache_enabled: Whether to use caching
        temperature: Temperature for generation
        
    Returns:
        Enhanced API documentation
    """
    provider = get_provider(provider_name)(api_key=api_key, model_name=model_name)
    cache = LLMCache() if cache_enabled else None
    rate_limiter = RateLimiter()
    
    # Enhance route descriptions
    for route in docs.routes:
        if not route.description or len(route.description.strip()) < 50:
            prompt = f"Generate a detailed description for this API endpoint:\nPath: {route.path}\nMethods: {', '.join(route.methods)}"
            
            if cache:
                cached_response = cache.get(
                    provider=provider_name,
                    model=model_name,
                    prompt=prompt,
                    temperature=temperature
                )
                if cached_response:
                    route.description = cached_response
                    continue
            
            response = None  # Initialize response variable
            for attempt in range(max_retries):
                try:
                    await rate_limiter.wait(provider_name)
                    response = await provider.generate(prompt, temperature=temperature)
                    route.description = response
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed to enhance route {route.path} after {max_retries} attempts: {e}")
                        continue
                    await asyncio.sleep(retry_delay * (attempt + 1))
            
            # Only cache if we got a valid response
            if cache and response is not None:
                cache.set(
                    provider=provider_name,
                    model=model_name,
                    prompt=prompt,
                    response=response,
                    temperature=temperature
                )
    
    return docs


async def get_llm_analysis(
    code: str, 
    api_key: str, 
    provider_name: str, 
    model_name: Optional[str] = None  # Optional with default None
) -> APIDocumentation:
    """Extract API documentation from code using LLM."""
    try:
        provider_class = get_provider(provider_name)
        provider = provider_class(
            api_key=api_key,
            model_name=model_name  # Remove fallback to default_model
        )
        
        logger.info(f"Initialized {provider_name} provider with model: {model_name}")
        
        system_prompt = """You are an expert FastAPI code analyzer. Analyze the code and provide comprehensive documentation.
Focus on:
1. Clear, detailed descriptions for each endpoint
2. Accurate parameter documentation
3. Response type information
4. Logical grouping with tags
5. Any security requirements

Return the documentation in this JSON format:
{
    "title": "API name",
    "description": "Overall API description",
    "version": "1.0.0",
    "routes": [
        {
            "path": "/path",
            "methods": ["GET"],
            "summary": "Clear summary",
            "description": "Detailed description of functionality",
            "parameters": [
                {
                    "name": "param_name",
                    "type": "path|query|body",
                    "required": true,
                    "description": "Clear parameter description"
                }
            ],
            "tags": ["logical_group"],
            "deprecated": false
        }
    ]
}"""

        response = await provider.generate(
            prompt=code,
            system_prompt=system_prompt,
            temperature=0.3
        )

        # Parse JSON response
        data = json.loads(response)
        
        # Convert routes with proper parameter handling
        routes = []
        for route_data in data.get("routes", []):
            # Convert parameters to match the model
            parameters = []
            for param in route_data.get("parameters", []):
                parameters.append(RouteParameter(
                    name=param["name"],
                    type=param["type"],
                    required=param.get("required", False),
                    description=param.get("description", ""),
                    data_type=param.get("data_type", "string")
                ))
            
            # Create route with converted parameters
            route = RouteInfo(
                path=route_data["path"],
                methods=route_data["methods"],
                summary=route_data.get("summary"),
                description=route_data.get("description"),
                parameters=parameters,
                tags=route_data.get("tags", []),
                deprecated=route_data.get("deprecated", False)
            )
            routes.append(route)
        
        # Create documentation
        docs = APIDocumentation(
            title=data.get("title", "FastAPI Application"),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            routes=routes
        )
        
        return docs

    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        return None