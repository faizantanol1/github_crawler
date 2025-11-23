"""PostgreSQL connection management."""

import psycopg2
from typing import Optional
from src.utils.logger import setup_logger
from src.utils.config import Config

logger = setup_logger(__name__)

class DatabaseConnection:
    """Manages PostgreSQL connections."""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.conn = None
    
    def connect(self):
        """Establish connection."""
        try:
            self.conn = psycopg2.connect(
                host=self.config.DB_HOST,
                port=self.config.DB_PORT,
                database=self.config.DB_NAME,
                user=self.config.DB_USER,
                password=self.config.DB_PASSWORD
            )
            logger.info(f'Connected to {self.config.DB_NAME}')
        except psycopg2.Error as e:
            logger.error(f'Connection failed: {e}')
            raise
    
    def disconnect(self):
        """Close connection."""
        if self.conn:
            self.conn.close()
            logger.info('Disconnected from database')
    
    def execute(self, query: str, params: tuple = ()):
        """Execute query."""
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, *args):
        self.disconnect()
