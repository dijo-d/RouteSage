from datetime import datetime, timedelta
from typing import Dict, Optional
import asyncio

class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.calls: Dict[str, list] = {}
    
    async def wait(self, provider: str):
        """Wait if rate limit is exceeded."""
        now = datetime.now()
        if provider not in self.calls:
            self.calls[provider] = []
        
        # Remove old timestamps
        self.calls[provider] = [ts for ts in self.calls[provider] 
                              if now - ts < timedelta(minutes=1)]
        
        if len(self.calls[provider]) >= self.calls_per_minute:
            wait_time = 60 - (now - self.calls[provider][0]).seconds
            await asyncio.sleep(wait_time)
            
        self.calls[provider].append(now)