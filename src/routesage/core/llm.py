from typing import Optional, Dict, Any, Set
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
    model_name: Optional[str] = None,  # Optional with default None
    strict_verification: bool = False  # Add verification flag
) -> APIDocumentation:
    """Extract API documentation from code using LLM."""
    try:
        # First, extract actual routes using AST parsing
        actual_routes = extract_routes_with_ast(code)
        
        provider_class = get_provider(provider_name)
        provider = provider_class(
            api_key=api_key,
            model_name=model_name
        )
        
        logger.info(f"Initialized {provider_name} provider with model: {model_name}")
        
        system_prompt = """You are an expert FastAPI code analyzer. Analyze the code and provide comprehensive documentation.
Focus on:
1. Clear, detailed descriptions for each endpoint
2. Accurate parameter documentation
3. Response type information
4. Logical grouping with tags
5. Any security requirements
6. Confidence score for each route (0.0-1.0)

IMPORTANT: ONLY document routes that are explicitly defined in the code. DO NOT invent or assume routes that aren't clearly defined.
For each route, provide a confidence score between 0.0 and 1.0 indicating how confident you are that this is a real route.

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
            "deprecated": false,
            "confidence_score": 0.95
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
        
        # Filter routes to only include those that actually exist in the code
        validated_routes = []
        skipped_routes = []
        
        for route_data in data.get("routes", []):
            route_path = route_data["path"]
            confidence_score = route_data.get("confidence_score", 0.7)  # Default to 0.7 if not provided
            
            # Skip low-confidence routes
            if confidence_score < 0.5:
                logger.warning(f"Skipping low-confidence route: {route_path} (score: {confidence_score})")
                skipped_routes.append((route_path, f"Low confidence score: {confidence_score}"))
                continue
                
            # Verify route exists in actual code
            if route_path in actual_routes:
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
                    path=route_path,
                    methods=route_data["methods"],
                    summary=route_data.get("summary"),
                    description=route_data.get("description"),
                    parameters=parameters,
                    tags=route_data.get("tags", []),
                    deprecated=route_data.get("deprecated", False),
                    confidence_score=confidence_score,
                    verified=True
                )
                validated_routes.append(route)
            else:
                message = f"Route not found in actual code"
                logger.warning(f"Skipping hallucinated route: {route_path} - {message}")
                skipped_routes.append((route_path, message))
                
                # If not using strict verification, include the route but mark as unverified
                if not strict_verification:
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
                    
                    # Create route with converted parameters but mark as unverified
                    route = RouteInfo(
                        path=route_path,
                        methods=route_data["methods"],
                        summary=route_data.get("summary", ""),
                        description=route_data.get("description", ""),
                        parameters=parameters,
                        tags=route_data.get("tags", []),
                        deprecated=route_data.get("deprecated", False),
                        confidence_score=confidence_score * 0.5,  # Reduce confidence for unverified routes
                        verified=False
                    )
                    validated_routes.append(route)
        
        # Log skipped routes for better error reporting
        if skipped_routes:
            logger.warning(f"Skipped {len(skipped_routes)} routes during verification:")
            for path, reason in skipped_routes:
                logger.warning(f"  - {path}: {reason}")
        
        # Create documentation with validated routes only
        docs = APIDocumentation(
            title=data.get("title", "FastAPI Application"),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            routes=validated_routes
        )
        
        return docs

    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        return None

def extract_routes_with_ast(code: str) -> Set[str]:
    """Extract FastAPI routes from code using AST parsing."""
    try:
        import ast
        import re
        
        # Pattern to match FastAPI route decorators - expanded to include router patterns
        route_pattern = re.compile(r'@(?:app|router|api_router|blueprint)\.(get|post|put|delete|patch|options|head|trace)\s*\(\s*[\'"]([^\'"]+)[\'"]')
        
        route_paths = set()
        
        tree = ast.parse(code)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                decorator_lines = []
                
                # Get the actual decorator lines from source
                for decorator in node.decorator_list:
                    if hasattr(decorator, 'lineno'):
                        start = decorator.lineno - 1
                        end = decorator.end_lineno if hasattr(decorator, 'end_lineno') else start + 1
                        
                        # Extract the lines from the source code
                        code_lines = code.splitlines()
                        if start < len(code_lines):
                            decorator_lines.extend(code_lines[start:end])
                
                # Check for FastAPI route decorators
                for dec_line in decorator_lines:
                    match = route_pattern.search(dec_line)
                    if match:
                        method, path = match.groups()
                        route_paths.add(path)
        
        return route_paths
    except Exception as e:
        logger.error(f"Failed to extract routes with AST: {e}")
        return set()