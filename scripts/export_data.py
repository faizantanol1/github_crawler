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

def main():
    try:
        with DatabaseConnection() as db:
            dao = RepositoryDAO(db)
            repos = dao.get_all()
        
        if not repos:
            logger.warning('No repositories to export')
            return
        
        # Export to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_file = f'repositories_{timestamp}.csv'
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=repos[0].keys())
            writer.writeheader()
            writer.writerows(repos)
        logger.info(f'Exported {len(repos)} repos to {csv_file}')
        
        # Export to JSON
        json_file = f'repositories_{timestamp}.json'
        with open(json_file, 'w') as f:
            json.dump(repos, f, indent=2, default=str)
        logger.info(f'Exported {len(repos)} repos to {json_file}')
    
    except Exception as e:
        logger.error(f'Export failed: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
