"""Data access layer for repositories."""

from typing import List, Dict, Optional
from datetime import datetime
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class RepositoryDAO:
    """Data access object for repositories."""
    
    def __init__(self, connection):
        self.connection = connection
    
    def upsert_batch(self, repositories: List[Dict]) -> int:
        """
        Efficiently upsert batch of repositories.
        
        Args:
            repositories: [{'github_id': str, 'full_name': str, 'stars': int}]
        
        Returns:
            Number of rows affected
        """
        if not repositories:
            return 0
        
        cursor = self.connection.conn.cursor()
        
        # Build single INSERT ON CONFLICT statement
        query = """
        INSERT INTO repositories (github_id, full_name, stars, last_crawled)
        VALUES %s
        ON CONFLICT (github_id) DO UPDATE SET
            stars = EXCLUDED.stars,
            last_crawled = EXCLUDED.last_crawled,
            updated_at = NOW()
        """
        
        values = [
            (
                repo['github_id'],
                repo['full_name'],
                repo['stars'],
                datetime.now()
            )
            for repo in repositories
        ]
        
        try:
            # Use executemany for efficiency
            for value in values:
                cursor.execute(
                    """
                    INSERT INTO repositories (github_id, full_name, stars, last_crawled)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (github_id) DO UPDATE SET
                        stars = EXCLUDED.stars,
                        last_crawled = EXCLUDED.last_crawled,
                        updated_at = NOW()
                    """,
                    value
                )
            
            self.connection.conn.commit()
            logger.info(f'Upserted {len(repositories)} repositories')
            return len(repositories)
        except Exception as e:
            self.connection.conn.rollback()
            logger.error(f'Upsert failed: {e}')
            raise
    
    def insert_metadata(self, repo_id: int, metadata_type: str, 
                       metadata_id: str, data: Dict) -> None:
        """Insert or update metadata."""
        cursor = self.connection.conn.cursor()
        
        query = """
        INSERT INTO repository_metadata (repo_id, metadata_type, metadata_id, data)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (repo_id, metadata_type, metadata_id) DO UPDATE SET
            data = EXCLUDED.data,
            updated_at = NOW()
        """
        
        try:
            cursor.execute(query, (repo_id, metadata_type, metadata_id, str(data)))
            self.connection.conn.commit()
        except Exception as e:
            self.connection.conn.rollback()
            logger.error(f'Metadata insert failed: {e}')
            raise
    
    def get_all(self, limit: int = 10000) -> List[Dict]:
        """Fetch all repositories."""
        cursor = self.connection.conn.cursor()
        cursor.execute(
            'SELECT github_id, full_name, stars, last_crawled FROM repositories LIMIT %s',
            (limit,)
        )
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'github_id': row[0],
                'full_name': row[1],
                'stars': row[2],
                'last_crawled': row[3]
            })
        return results
