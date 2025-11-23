#!/usr/bin/env python3
"""Crawl GitHub repositories and store star counts."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.crawler.github_client import GitHubClient
from src.crawler.fetcher import Fetcher
from src.database.connection import DatabaseConnection
from src.database.repository import RepositoryDAO
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    try:
        config = Config()
        
        if not config.GITHUB_TOKEN:
            logger.error('GITHUB_TOKEN not set')
            sys.exit(1)
        
        logger.info(f'Starting crawl (target: {config.TARGET_REPOS})...')
        
        # Initialize components
        client = GitHubClient(config.GITHUB_TOKEN)
        fetcher = Fetcher(client)
        
        with DatabaseConnection(config) as db:
            dao = RepositoryDAO(db)
            
            # Fetch and store repositories in batches
            batch = []
            batch_size = 100
            
            for repo in fetcher.fetch_repositories(config.TARGET_REPOS):
                batch.append(repo)
                
                if len(batch) >= batch_size:
                    dao.upsert_batch(batch)
                    batch = []
            
            # Upsert remaining
            if batch:
                dao.upsert_batch(batch)
        
        logger.info(f'Crawl complete: {fetcher.total_fetched} repositories')
    
    except Exception as e:
        logger.error(f'Crawl failed: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
