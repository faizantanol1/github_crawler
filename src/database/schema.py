"""Database schema definitions."""

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class Schema:
    """Manages database schema."""
    
    REPOSITORIES_TABLE = """
    CREATE TABLE IF NOT EXISTS repositories (
        id BIGSERIAL PRIMARY KEY,
        github_id VARCHAR(255) UNIQUE NOT NULL,
        full_name VARCHAR(255) NOT NULL,
        stars INTEGER NOT NULL,
        last_crawled TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    """
    
    METADATA_TABLE = """
    CREATE TABLE IF NOT EXISTS repository_metadata (
        id BIGSERIAL PRIMARY KEY,
        repo_id BIGINT REFERENCES repositories(id) ON DELETE CASCADE,
        metadata_type VARCHAR(50) NOT NULL,
        metadata_id VARCHAR(255) NOT NULL,
        data JSONB,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),
        UNIQUE (repo_id, metadata_type, metadata_id)
    );
    """
    
    INDEXES = [
        "CREATE INDEX IF NOT EXISTS idx_full_name ON repositories(full_name);",
        "CREATE INDEX IF NOT EXISTS idx_last_crawled ON repositories(last_crawled);",
        "CREATE INDEX IF NOT EXISTS idx_metadata_type ON repository_metadata(metadata_type);",
        "CREATE INDEX IF NOT EXISTS idx_metadata_repo ON repository_metadata(repo_id);",
    ]
    
    @staticmethod
    def create_all(connection):
        """Create all tables and indexes."""
        cursor = connection.conn.cursor()
        
        try:
            cursor.execute(Schema.REPOSITORIES_TABLE)
            logger.info('Created repositories table')
            
            cursor.execute(Schema.METADATA_TABLE)
            logger.info('Created repository_metadata table')
            
            for index_sql in Schema.INDEXES:
                cursor.execute(index_sql)
            logger.info('Created indexes')
            
            connection.conn.commit()
        except Exception as e:
            connection.conn.rollback()
            logger.error(f'Schema creation failed: {e}')
            raise
