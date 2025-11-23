"""Configuration management."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    """Application configuration."""
    
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
    GITHUB_GRAPHQL_URL = 'https://api.github.com/graphql'
    
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '5432'))
    DB_NAME = os.getenv('DB_NAME', 'github_crawler')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    BATCH_SIZE = 100  # Repos per GraphQL query
    TARGET_REPOS = 100000  # Total repos to fetch
