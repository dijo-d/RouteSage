# routesage/export/__init__.py
from typing import Dict, Type, Any

from .markdown_exporter import MarkdownExporter
from .json_exporter import JSONExporter


# Registry of available exporters
_EXPORTERS = {
    "markdown": MarkdownExporter,
    "json": JSONExporter
}


def get_exporter(format_name: str, **kwargs: Any):
    """
    Get an exporter instance by format name.
    
    Args:
        format_name: Format name (markdown, json, etc.)
        **kwargs: Additional arguments to pass to the exporter constructor
        
    Returns:
        Exporter instance
        
    Raises:
        ValueError: If the format is not supported
    """
    exporter_class = _EXPORTERS.get(format_name.lower())
    if exporter_class is None:
        available = ", ".join(_EXPORTERS.keys())
        raise ValueError(f"Export format '{format_name}' not supported. Available formats: {available}")
    
    return exporter_class(**kwargs)


def list_formats() -> list:
    """
    List all available export formats.
    
    Returns:
        List of format names
    """
    return list(_EXPORTERS.keys())