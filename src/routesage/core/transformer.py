import ast
from .models import APIDocumentation

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