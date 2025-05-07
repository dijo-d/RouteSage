# routesage/core/analyzer.py
import ast
import os
import inspect
import importlib.util
import sys
from typing import List, Dict, Any, Optional, Tuple, Set, Union
import logging
from pathlib import Path
import re

from .models import (
    RouteInfo, 
    RouteParameter, 
    RouteParameterType, 
    RouteResponse,
    APIDocumentation
)
from .llm import get_llm_analysis
from ..utils.logger import get_logger
from .transformer import FastAPIDocumentationTransformer

logger = logging.getLogger(__name__)

class FastAPIAnalyzer:
    """Analyzer for FastAPI applications to extract route information."""
    
    def __init__(self, app_path: Union[str, Path]):
        """
        Initialize the analyzer.
        
        Args:
            app_path: Path to the FastAPI application file or directory
        """
        self.app_path = Path(app_path).resolve()
        
    async def analyze(self, api_key: str, provider_name: str = "openai", model_name: Optional[str] = None) -> APIDocumentation:
        """Analyze the FastAPI application using LLM-first approach."""
        try:
            with open(self.app_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Ensure we're using the correct provider
            logger.info(f"Using LLM provider: {provider_name} with model: {model_name}")
            
            # Get LLM analysis with explicit provider and model
            llm_docs = await get_llm_analysis(
                content, 
                api_key=api_key,
                provider_name=provider_name,
                model_name=model_name
            )
            
            if llm_docs and llm_docs.routes:
                logger.info("Successfully extracted API documentation using LLM")
                
                # Update the original FastAPI code with LLM-generated documentation
                updated_content = self._update_fastapi_code(content, llm_docs)
                
                # Write back the updated code
                with open(self.app_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                logger.info("FastAPI code updated with LLM-generated documentation")
                return llm_docs
            
            logger.warning("LLM analysis failed to find endpoints")
            return APIDocumentation(
                title="FastAPI Application",
                description="Failed to analyze application",
                version="1.0.0",
                routes=[]
            )
                
        except Exception as e:
            logger.error(f"Failed to analyze FastAPI application: {e}")
            raise

    def _update_fastapi_code(self, content: str, docs: APIDocumentation) -> str:
        """Update FastAPI code with LLM-generated documentation."""
        import ast
        import astor
        
        try:
            tree = ast.parse(content)
            transformer = FastAPIDocumentationTransformer(docs)
            updated_tree = transformer.visit(tree)
            return astor.to_source(updated_tree)
        except Exception as e:
            logger.error(f"Failed to update FastAPI code: {e}")
            return content

class FastAPIDocumentationTransformer(ast.NodeTransformer):
    """AST transformer to update FastAPI route decorators with documentation."""
    
    def __init__(self, docs: APIDocumentation):
        self.docs = docs
        self.route_map = {route.path: route for route in docs.routes}
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Visit function definitions and update route decorators."""
        self.generic_visit(node)
        
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                if decorator.func.attr in ['get', 'post', 'put', 'delete', 'patch']:
                    # Get the route path from the decorator
                    path_arg = decorator.args[0] if decorator.args else None
                    if path_arg and isinstance(path_arg, ast.Str):
                        route_path = path_arg.s
                        route_info = self.route_map.get(route_path)
                        
                        if route_info:
                            # Update or add description and tags keywords
                            new_keywords = []
                            has_description = False
                            has_tags = False
                            
                            for kw in decorator.keywords:
                                if kw.arg == 'description':
                                    kw.value = ast.Str(s=route_info.description)
                                    has_description = True
                                elif kw.arg == 'tags':
                                    kw.value = ast.List(elts=[ast.Str(s=tag) for tag in route_info.tags])
                                    has_tags = True
                                new_keywords.append(kw)
                            
                            if not has_description and route_info.description:
                                new_keywords.append(
                                    ast.keyword(arg='description', value=ast.Str(s=route_info.description))
                                )
                            
                            if not has_tags and route_info.tags:
                                new_keywords.append(
                                    ast.keyword(arg='tags', value=ast.List(
                                        elts=[ast.Str(s=tag) for tag in route_info.tags]
                                    ))
                                )
                            decorator.keywords = new_keywords
        
        return node
    
    def _analyze_directory(self, directory: Path) -> APIDocumentation:
        """
        Analyze all Python files in a directory recursively.
        
        Args:
            directory: Directory path
            
        Returns:
            API documentation object
        """
        routes = []
        tags = {}
        
        # Get app title and description by looking for FastAPI instantiation
        title = "FastAPI Application"
        description = None
        version = "1.0.0"
        
        # Walk through the directory and process Python files
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    try:
                        doc = self._analyze_file(file_path)
                        routes.extend(doc.routes)
                        tags.update(doc.tags)
                        
                        # If we find the main FastAPI app, get its metadata
                        if doc.title != "FastAPI Application":
                            title = doc.title
                            description = doc.description
                            version = doc.version
                    except Exception as e:
                        logger.error(f"Error analyzing file {file_path}: {e}")
        
        return APIDocumentation(
            title=title,
            description=description,
            version=version,
            routes=routes,
            tags=tags
        )
    
    def _analyze_file(self, file_path: Path) -> APIDocumentation:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            logger.warning(f"Failed to read {file_path} with UTF-8 encoding, trying with system default")
            with open(file_path, 'r') as f:
                content = f.read()
        
        # Parse the file as an AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            return APIDocumentation(title="FastAPI Application")
        
        # Extract app information and routes
        app_info = self._extract_app_info(tree, content)
        routes = self._extract_routes(tree, content, file_path)
        
        return APIDocumentation(
            title=app_info.get("title", "FastAPI Application"),
            description=app_info.get("description"),
            version=app_info.get("version", "1.0.0"),
            routes=routes,
            tags=app_info.get("tags", {})
        )
    
    def _extract_app_info(self, tree: ast.Module, content: str) -> Dict[str, Any]:
        """
        Extract FastAPI app information.
        
        Args:
            tree: AST of the Python file
            content: File content as a string
            
        Returns:
            Dictionary with app information
        """
        app_info = {
            "title": "FastAPI Application",
            "description": None,
            "version": "1.0.0",
            "tags": {}
        }
        
        # Look for FastAPI instantiation
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and hasattr(node, 'func'):
                func = node.func
                if (isinstance(func, ast.Name) and func.id == 'FastAPI') or \
                   (isinstance(func, ast.Attribute) and func.attr == 'FastAPI'):
                    # Extract kwargs from the FastAPI constructor
                    for kw in node.keywords:
                        if kw.arg == 'title' and isinstance(kw.value, ast.Str):
                            app_info["title"] = kw.value.s
                        elif kw.arg == 'description' and isinstance(kw.value, ast.Str):
                            app_info["description"] = kw.value.s
                        elif kw.arg == 'version' and isinstance(kw.value, ast.Str):
                            app_info["version"] = kw.value.s
        
        return app_info
    
    def _extract_routes(self, tree: ast.AST, content: str, file_path: str) -> List[RouteInfo]:
        routes = []
        
        # Pattern to match FastAPI route decorators
        route_pattern = re.compile(r'@app\.(get|post|put|delete|patch|options|head|trace)\s*\(\s*[\'"]([^\'"]+)[\'"]')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                route_info = None
                decorator_lines = []
                
                # Get the actual decorator lines from source
                for decorator in node.decorator_list:
                    start = decorator.lineno - 1
                    end = decorator.end_lineno if hasattr(decorator, 'end_lineno') else start + 1
                    decorator_lines.extend(content.splitlines()[start:end])
                
                # Check for FastAPI route decorators
                for dec_line in decorator_lines:
                    match = route_pattern.search(dec_line)
                    if match:
                        method, path = match.groups()
                        
                        # Extract docstring for description
                        description = ast.get_docstring(node) or ""
                        
                        # Create route info
                        route_info = RouteInfo(
                            path=path,
                            methods=[method.upper()],
                            description=description,
                            summary=description.split('\n')[0] if description else "",
                            parameters=[],
                            tags=[],
                            deprecated=False
                        )
                        
                        # Auto-generate tags from first path segment
                        path_segments = [s for s in path.split('/') if s and not s.startswith('{')]
                        if path_segments:
                            route_info.tags = [path_segments[0]]
                        
                        routes.append(route_info)
                        break
    
        # Always return a list, even if empty
        return routes or []
    
    def _analyze_with_ast(self, content: str) -> APIDocumentation:
        """
        Analyze FastAPI code using AST parsing.
        
        Args:
            content: Source code content
            
        Returns:
            API documentation object
        """
        try:
            tree = ast.parse(content)
            
            # Extract app information and routes
            app_info = self._extract_app_info(tree, content)
            routes = self._extract_routes(tree, content, str(self.app_path))
            
            return APIDocumentation(
                title=app_info.get("title", "FastAPI Application"),
                description=app_info.get("description"),
                version=app_info.get("version", "1.0.0"),
                routes=routes,
                tags=app_info.get("tags", {})
            )
        except Exception as e:
            logger.error(f"AST analysis failed: {e}")
            return APIDocumentation(
                title="FastAPI Application",
                description="Failed to analyze application",
                version="1.0.0",
                routes=[],
                tags={}
            )  # Added closing parenthesis here