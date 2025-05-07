# routesage/core/config.py
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Configuration manager for RouteSage."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration.
        
        Args:
            config_path: Path to the config file. If None, uses ~/.routesage/config.json
        """
        if config_path is None:
            home_dir = os.path.expanduser("~")
            config_dir = os.path.join(home_dir, ".routesage")
            
            # Create the config directory if it doesn't exist
            Path(config_dir).mkdir(parents=True, exist_ok=True)
            
            config_path = os.path.join(config_dir, "config.json")
        
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load the configuration from disk."""
        if not self.config_path.exists():
            return self._create_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If there's any issue loading the config, return defaults
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create and save a default configuration."""
        default_config = {
            "default_provider": "openai",
            "default_model": "gpt-3.5-turbo",
            "cache_enabled": True,
            "providers": {
                "openai": {
                    "api_key": "",
                    "default_model": "gpt-3.5-turbo"
                },
                "claude": {
                    "api_key": "",
                    "default_model": "claude-3-sonnet-20240229"
                },
                "gemini": {
                    "api_key": "",
                    "default_model": "gemini-1.5-pro"
                },
                "deepseek": {
                    "api_key": "",
                    "default_model": "deepseek-coder"
                }
            },
            "export": {
                "default_format": "markdown",
                "output_dir": "./docs"
            }
        }
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
        except IOError:
            # Handle the case where writing the config fails
            pass
            
        return default_config
    
    def save(self) -> bool:
        """
        Save the current configuration to disk.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
            return True
        except IOError:
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key (supports dot notation for nested keys)
            default: Default value if key is not found
            
        Returns:
            Configuration value
        """
        parts = key.split('.')
        value = self._config
        
        for part in parts:
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key (supports dot notation for nested keys)
            value: Value to set
        """
        parts = key.split('.')
        config = self._config
        
        # Navigate to the nested dict containing the key to update
        for part in parts[:-1]:
            if part not in config:
                config[part] = {}
            config = config[part]
        
        # Update the value
        config[parts[-1]] = value
        
        # Save the updated config
        self.save()