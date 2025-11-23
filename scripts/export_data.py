#!/usr/bin/env python3
"""Export database to CSV and JSON."""


import sys
import os
import csv
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import DatabaseConnection
from src.database.repository import RepositoryDAO
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Folder to store all exports
EXPORT_DIR = "repositories"  # You can change this to 'exports' if you prefer
os.makedirs(EXPORT_DIR, exist_ok=True)  # Create folder if it doesn't exist

def main():
    try:
        with DatabaseConnection() as db:
            dao = RepositoryDAO(db)
            repos = dao.get_all()
        
        if not repos:
            logger.warning('No repositories to export')
            return
        
        # Timestamp for filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Export to CSV
        csv_file = os.path.join(EXPORT_DIR, f'repositories_{timestamp}.csv')
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=repos[0].keys())
            writer.writeheader()
            writer.writerows(repos)
        logger.info(f'Exported {len(repos)} repos to {csv_file}')
    
    except Exception as e:
        logger.error(f'Export failed: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()