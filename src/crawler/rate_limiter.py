"""Rate limiter for GitHub API."""

import time
from typing import Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class RateLimiter:
    """Manages GitHub API rate limits."""
    
    def __init__(self):
        self.remaining = 5000
        self.reset_at = 0
    
    def update_from_response(self, headers: Dict) -> None:
        """Update rate limit from response headers."""
        self.remaining = int(headers.get('x-ratelimit-remaining', 5000))
        self.reset_at = int(headers.get('x-ratelimit-reset', 0))
    
    def wait_if_needed(self) -> None:
        """Wait if rate limit approaching."""
        if self.remaining < 100:
            wait_time = max(0, self.reset_at - time.time()) + 5
            logger.warning(f'Rate limit low. Waiting {wait_time}s...')
            time.sleep(wait_time)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def make_request_with_retry(func, *args, **kwargs):
    """Make request with exponential backoff retry."""
    return func(*args, **kwargs)
