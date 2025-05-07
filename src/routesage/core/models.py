# routesage/core/models.py
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class RouteParameterType(str, Enum):
    """Types of parameters in a FastAPI route."""
    PATH = "path"
    QUERY = "query"
    BODY = "body"
    HEADER = "header"
    COOKIE = "cookie"


class RouteParameter(BaseModel):
    """Information about a route parameter."""
    name: str
    type: str
    required: bool = False
    description: Optional[str] = None
    data_type: Optional[str] = "string"


class RouteResponse(BaseModel):
    """Information about a route response."""
    status_code: int
    description: Optional[str] = None
    data_model: Optional[str] = None


class RouteInfo(BaseModel):
    """Information about a FastAPI route."""
    path: str
    methods: List[str]
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: List[RouteParameter] = Field(default_factory=list)
    responses: Dict[int, RouteResponse] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    deprecated: bool = False
    source_file: Optional[str] = None
    line_number: Optional[int] = None


class APIDocumentation(BaseModel):
    """Complete API documentation."""
    title: str
    description: Optional[str] = None
    version: str = "1.0.0"
    routes: List[RouteInfo] = Field(default_factory=list)
    tags: Dict[str, str] = Field(default_factory=dict)