# routesage/export/markdown_exporter.py
from typing import TextIO, List, Dict, Any
import os
from datetime import datetime
from pathlib import Path

from ..core.models import APIDocumentation, RouteInfo, RouteParameterType


class MarkdownExporter:
    """Exports API documentation to Markdown format."""
    
    def __init__(self, output_dir: str = "./docs"):
        """
        Initialize the exporter.
        
        Args:
            output_dir: Directory to write output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(self, docs: APIDocumentation) -> Path:
        """Export documentation to Markdown."""
        # Create filename based on title
        safe_title = "".join(c if c.isalnum() else "_" for c in docs.title.lower())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_title}_{timestamp}.md"
        file_path = self.output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"# {docs.title}\n\n")
            if docs.description:
                f.write(f"{docs.description}\n\n")
            f.write(f"**Version:** {docs.version}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Write table of contents
            f.write("## Table of Contents\n\n")
            
            # Group routes by tags
            tag_groups = {}
            for route in docs.routes:
                tag = route.tags[0] if route.tags else "Other"
                if tag not in tag_groups:
                    tag_groups[tag] = []
                tag_groups[tag].append(route)
            
            # Write TOC with tags and routes
            for tag, routes in tag_groups.items():
                f.write(f"### {tag}\n")
                for route in routes:
                    methods = ", ".join(route.methods)
                    f.write(f"- [{methods} {route.path}](#{route.path.replace('/', '-').lstrip('-')})\n")
                f.write("\n")
            
            f.write("\n---\n\n")
            
            # Write detailed documentation
            for tag, routes in tag_groups.items():
                f.write(f"## {tag}\n\n")
                
                for route in routes:
                    anchor = route.path.replace('/', '-').lstrip('-')
                    methods = ", ".join(route.methods)
                    f.write(f"### {methods} {route.path} {'{#' + anchor + '}'}\n\n")
                    
                    if route.summary:
                        f.write(f"**Summary:** {route.summary}\n\n")
                    
                    if route.description:
                        f.write(f"{route.description}\n\n")
                    
                    if route.parameters:
                        f.write("#### Parameters\n\n")
                        f.write("| Name | Type | Required | Description |\n")
                        f.write("|------|------|----------|-------------|\n")
                        for param in route.parameters:
                            required = "✓" if param.required else "✗"
                            f.write(f"| {param.name} | {param.type} | {required} | {param.description} |\n")
                        f.write("\n")
                    
                    if route.deprecated:
                        f.write("⚠️ **Deprecated**\n\n")
                    
                    f.write("---\n\n")
        
        return file_path