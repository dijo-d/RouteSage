import unittest
import os
import sys
import ast
from pathlib import Path
import re
from typing import Set, List, Dict

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from routesage.core.models import APIDocumentation, RouteInfo
from routesage.core.llm import extract_routes_with_ast


class TestRouteVerification(unittest.TestCase):
    """Test route verification functionality."""
    
    def test_route_extraction(self):
        """Test that route extraction correctly identifies routes."""
        # Test with app pattern
        code_app = """
@app.get("/users")
def get_users():
    return {"users": []}
        """
        routes = extract_routes_with_ast(code_app)
        self.assertIn("/users", routes)
        
        # Test with router pattern
        code_router = """
@router.post("/items")
def create_item():
    return {"status": "created"}
        """
        routes = extract_routes_with_ast(code_router)
        self.assertIn("/items", routes)
        
        # Test with api_router pattern
        code_api_router = """
@api_router.delete("/products/{id}")
def delete_product(id: int):
    return {"status": "deleted"}
        """
        routes = extract_routes_with_ast(code_api_router)
        self.assertIn("/products/{id}", routes)
    
    def test_confidence_filtering(self):
        """Test that routes are filtered by confidence score."""
        # Create a sample documentation with routes of varying confidence
        docs = APIDocumentation(
            title="Test API",
            description="Test API Description",
            version="1.0.0",
            routes=[
                RouteInfo(
                    path="/high-confidence",
                    methods=["GET"],
                    confidence_score=0.9
                ),
                RouteInfo(
                    path="/medium-confidence",
                    methods=["POST"],
                    confidence_score=0.6
                ),
                RouteInfo(
                    path="/low-confidence",
                    methods=["DELETE"],
                    confidence_score=0.3
                )
            ]
        )
        
        # Filter routes with confidence >= 0.7
        high_confidence_routes = [r for r in docs.routes if r.confidence_score >= 0.7]
        self.assertEqual(len(high_confidence_routes), 1)
        self.assertEqual(high_confidence_routes[0].path, "/high-confidence")
        
        # Filter routes with confidence >= 0.5
        medium_confidence_routes = [r for r in docs.routes if r.confidence_score >= 0.5]
        self.assertEqual(len(medium_confidence_routes), 2)
        
        # Filter routes with confidence >= 0.2
        all_routes = [r for r in docs.routes if r.confidence_score >= 0.2]
        self.assertEqual(len(all_routes), 3)
    
    def test_verification_flag(self):
        """Test that the verification flag works correctly."""
        # Create a sample documentation with verified and unverified routes
        docs = APIDocumentation(
            title="Test API",
            description="Test API Description",
            version="1.0.0",
            routes=[
                RouteInfo(
                    path="/verified",
                    methods=["GET"],
                    verified=True
                ),
                RouteInfo(
                    path="/unverified",
                    methods=["POST"],
                    verified=False
                )
            ]
        )
        
        # Filter verified routes
        verified_routes = [r for r in docs.routes if r.verified]
        self.assertEqual(len(verified_routes), 1)
        self.assertEqual(verified_routes[0].path, "/verified")
        
        # Filter unverified routes
        unverified_routes = [r for r in docs.routes if not r.verified]
        self.assertEqual(len(unverified_routes), 1)
        self.assertEqual(unverified_routes[0].path, "/unverified")


if __name__ == "__main__":
    unittest.main()