# routesage/core/cache.py
import os
import json
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path


class LLMCache:
    """Cache for LLM responses to avoid redundant API calls."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the cache.
        
        Args:
            cache_dir: Directory to store cache files. If None, uses ~/.routesage/cache
        """
        if cache_dir is None:
            home_dir = os.path.expanduser("~")
            cache_dir = os.path.join(home_dir, ".routesage", "cache")
            
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_cache_key(self, provider: str, model: str, prompt: str, 
                      system_prompt: Optional[str], temperature: float) -> str:
        """
        Generate a cache key based on request parameters.
        
        Args:
            provider: Provider name
            model: Model name
            prompt: User prompt
            system_prompt: System prompt
            temperature: Temperature value
            
        Returns:
            Cache key as a string
        """
        # Create a string to hash
        hash_content = f"{provider}::{model}::{prompt}::{system_prompt}::{temperature}"
        return hashlib.md5(hash_content.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the path to the cache file for the given key."""
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, provider: str, model: str, prompt: str, 
           system_prompt: Optional[str] = None, temperature: float = 0.7) -> Optional[str]:
        """
        Get a cached response if available.
        
        Args:
            provider: Provider name
            model: Model name
            prompt: User prompt
            system_prompt: System prompt
            temperature: Temperature value
            
        Returns:
            Cached response text or None if not found
        """
        cache_key = self._get_cache_key(provider, model, prompt, system_prompt, temperature)
        cache_path = self._get_cache_path(cache_key)
        
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)
                    return cache_data.get("response")
            except (json.JSONDecodeError, KeyError, IOError):
                # If there's any issue reading the cache, return None
                return None
        
        return None
    
    def set(self, provider: str, model: str, prompt: str, response: str,
           system_prompt: Optional[str] = None, temperature: float = 0.7) -> None:
        if not response or not response.strip():
            return  # Don't cache empty responses
            
        if len(response) > 1_000_000:  # 1MB limit
            return  # Don't cache extremely large responses

        cache_key = self._get_cache_key(provider, model, prompt, system_prompt, temperature)
        cache_path = self._get_cache_path(cache_key)
        
        cache_data = {
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "response": response
        }
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except IOError:
            # Handle the case where writing to the cache fails
            pass
    
    def clear(self) -> int:
        """
        Clear all cached items.
        
        Returns:
            Number of items cleared
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except IOError:
                pass
                
        return count