# GitHub Crawler

Crawls 100,000 GitHub repositories using GraphQL API and stores star counts in PostgreSQL with efficient daily updates.

## Features

- **GraphQL API Integration:** Anti-corruption layer for clean data transformation
- **Rate Limit Handling:** Respects GitHub's 5000 points/hour limit with exponential backoff
- **PostgreSQL Storage:** Flexible JSONB schema for future metadata (issues, PRs, comments, etc.)
- **Batch Processing:** Efficient upsert operations for high-throughput crawling
- **GitHub Actions Pipeline:** Fully automated daily crawl with PostgreSQL service container
- **Data Export:** CSV and JSON exports of crawled data

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GITHUB_TOKEN=<your_token>
export DB_HOST=localhost
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_NAME=github_crawler

# Setup database
python scripts/setup_database.py

# Run crawler
python scripts/crawl_stars.py

# Export data
python scripts/export_data.py
```

## Architecture

```
GitHub API (GraphQL)
    ↓
GitHubClient (anti-corruption)
    ↓
Fetcher (orchestration)
    ↓
RepositoryDAO (data access)
    ↓
PostgreSQL (repositories + metadata)
```

## Schema

**repositories table:**
- `github_id` (unique identifier)
- `full_name` (owner/repo)
- `stars` (current count)
- `last_crawled` (timestamp for efficient updates)
- `created_at`, `updated_at`

**repository_metadata table (JSONB):**
- Flexible storage for issues, PRs, commits, comments, reviews, CI checks
- Single row per PR = efficient updates even with 10→20 comments

See `ARCHITECTURE.md` for scaling strategy and schema evolution.

## GitHub Actions

The pipeline:
1. Spins up PostgreSQL service container
2. Creates schema
3. Runs crawler for ~100K repos
4. Exports to CSV/JSON
5. Uploads artifacts

No private secrets required - uses default GitHub token.