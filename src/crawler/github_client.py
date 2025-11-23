"""Anti-corruption layer for GitHub API."""

import requests
from typing import Dict, List, Optional
from src.utils.logger import setup_logger
from src.utils.config import Config
from src.crawler.rate_limiter import RateLimiter, make_request_with_retry

logger = setup_logger(__name__)

class GitHubClient:
    """GitHub GraphQL API client with anti-corruption layer."""
    
    BASE_URL = "https://api.github.com/graphql"
    
    # Query with inline fragments for union type
    SEARCH_QUERY = """
    query ($first: Int!, $after: String) {
        search(query: "stars:>0 sort:stars-desc", type: REPOSITORY, first: $first, after: $after) {
            edges {
                node {
                    ... on Repository {
                        databaseId
                        nameWithOwner
                        stargazerCount
                    }
                }
                cursor
            }
            pageInfo {
                endCursor
                hasNextPage
            }
            repositoryCount
        }
        rateLimit {
            remaining
            resetAt
        }
    }
    """
    
    def __init__(self, token: str):
        self.token = token
        self.rate_limiter = RateLimiter()
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        })
    
    def fetch_repositories(self, batch_size: int = 100, cursor: Optional[str] = None) -> Dict:
        """
        Fetch batch of repositories.
        
        Returns:
            {
                'repos': [{'id': str, 'name': str, 'stars': int}],
                'cursor': str or None,
                'has_next': bool
            }
        """
        def _fetch():
            payload = {
                'query': self.SEARCH_QUERY,
                'variables': {'first': batch_size, 'after': cursor}
            }
            
            response = make_request_with_retry(
                self.session.post,
                self.BASE_URL,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        
        self.rate_limiter.wait_if_needed()
        data = _fetch()
        
        # Handle errors
        if 'errors' in data:
            logger.error(f"GraphQL error: {data['errors']}")
            raise Exception(f"GraphQL error: {data['errors']}")
        
        # Update rate limits
        if 'data' in data and 'rateLimit' in data['data']:
            self.rate_limiter.remaining = data['data']['rateLimit']['remaining']
        
        # Anti-corruption: transform GitHub response to domain model
        search_data = data['data']['search']
        repos = []
        
        for edge in search_data.get('edges', []):
            node = edge.get('node', {})
            # Skip null nodes or non-Repository results
            if node and node.get('databaseId'):
                repos.append({
                    'id': node['databaseId'],
                    'name': node['nameWithOwner'],
                    'stars': node['stargazerCount']
                })
        
        return {
            'repos': repos,
            'cursor': search_data['pageInfo'].get('endCursor'),
            'has_next': search_data['pageInfo'].get('hasNextPage', False)
        }
