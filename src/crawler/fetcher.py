"""Main crawling orchestration."""

from typing import Generator, Tuple
from src.crawler.github_client import GitHubClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class Fetcher:
    """Orchestrates repository fetching."""
    
    def __init__(self, client: GitHubClient):
        self.client = client
        self.total_fetched = 0
    
    def fetch_repositories(self, target: int = 100000) -> Generator[dict, None, None]:
        """
        Fetch repositories in batches.
        
        Yields:
            {'github_id': str, 'full_name': str, 'stars': int}
        """
        cursor = None
        batch_count = 0
        
        while self.total_fetched < target:
            batch_count += 1
            logger.info(f'Fetching batch {batch_count} (total: {self.total_fetched})...')
            
            result = self.client.fetch_repositories(batch_size=100, cursor=cursor)
            
            for repo in result['repos']:
                yield {
                    'github_id': str(repo['id']),
                    'full_name': repo['name'],
                    'stars': repo['stars']
                }
                self.total_fetched += 1
                
                if self.total_fetched >= target:
                    break
            
            if not result['has_next']:
                logger.info('No more repositories available')
                break
            
            cursor = result['cursor']
        
        logger.info(f'Fetch complete: {self.total_fetched} repositories')
