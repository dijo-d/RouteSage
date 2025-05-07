# routesage/export/json_exporter.py
import json
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from ..core.models import APIDocumentation


class JSONExporter:
    """Exports API documentation to JSON format."""
    
    def __init__(self, output_dir: str = "./docs"):
        """
        Initialize the exporter.
        
        Args:
            output_dir: Directory to write output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(self, docs: APIDocumentation) -> Path:
        """
        Export documentation to JSON.
        
        Args:
            docs: API documentation object
            
        Returns:
            Path to the generated file
        """
        # Create filename based on title
        safe_title = "".join(c if c.isalnum() else "_" for c in docs.title.lower())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_title}_{timestamp}.json"
        file_path = self.output_dir / filename
        
        # Convert Pydantic models to dict
        docs_dict = docs.dict()
        
        # Add generation timestamp
        docs_dict["generated_at"] = datetime.now().isoformat()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(docs_dict, f, indent=2)
        
        return file_path