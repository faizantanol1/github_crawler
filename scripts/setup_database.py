#!/usr/bin/env python3
"""Setup database schema."""

import sys
import os
import psycopg2
from psycopg2 import sql

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import DatabaseConnection
from src.database.schema import Schema
from src.utils.logger import setup_logger
from src.utils.config import Config

logger = setup_logger(__name__)

def create_database_if_not_exists():
    """Create database if it doesn't exist (for local development)."""
    config = Config()
    
    try:
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database='postgres',
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (config.DB_NAME,)
        )
        
        if not cursor.fetchone():
            logger.info(f'Creating database {config.DB_NAME}...')
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(config.DB_NAME)
            ))
            logger.info(f'Database {config.DB_NAME} created')
        else:
            logger.info(f'Database {config.DB_NAME} already exists')
        
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        logger.warning(f'Could not verify database: {e}')

def main():
    try:
        logger.info('Setting up database...')
        # Create database only for local development
        create_database_if_not_exists()
        
        # Create tables
        with DatabaseConnection() as conn:
            Schema.create_all(conn)
        logger.info('Database setup complete')
    except Exception as e:
        logger.error(f'Setup failed: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
