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
# Architecture & Scaling Analysis

## Current Design (100K Repos)

**Schema:** Simple 2-table design optimized for frequent updates
- `repositories`: Core data (id, name, stars, last_crawled)
- `repository_metadata`: JSONB for flexible future data

**Rate Limiting:** Respects GitHub's 5000 points/hour GraphQL limit
**Batch Processing:** Inserts 100 repos at a time for efficiency

---

## Scaling to 500M Repositories

### 1. **Partitioning Strategy**
```sql
-- Partition by crawl date for rolling window deletion
CREATE TABLE repositories (
    ...
) PARTITION BY RANGE (last_crawled);
```
**Why:** Keep active data hot, archive old data easily

### 2. **Concurrent Crawlers**
- Run 10-20 parallel crawlers across different GitHub search queries
- Each crawler maintains independent rate limiter
- Distribute via message queue (Redis/Kafka)

### 3. **Database Optimization**
```sql
-- Columnar storage (Citus extension)
CREATE TABLE repositories_distributed (
    ...
) USING citus_partitioned_table;
```
- Use Citus PostgreSQL for sharding across multiple nodes
- Index only on frequently queried columns

### 4. **Change Data Capture**
- Instead of polling all repos daily, use CDC to capture only changes
- Store deltas incrementally (avoid full table rewrites)

### 5. **Archive Strategy**
- Move repos with no star changes in 30 days to cold storage
- Keep only recently active repos in hot database

**Estimated Time:** 500M repos at 100/sec = ~58 days with 1 crawler. With 10 parallel crawlers = ~6 days

---

## Future Metadata Schema Evolution

**Problem:** PRs can have 10 comments today, 20 tomorrow. Updating each comment row is expensive.

**Solution:** JSONB document per PR
```sql
CREATE TABLE repository_metadata (
    repo_id BIGINT,
    metadata_type VARCHAR(50),  -- 'issue', 'pr', 'commit'
    metadata_id VARCHAR(255),
    data JSONB,                 -- { comments: [...], reviews: [...], commits: [...] }
    updated_at TIMESTAMP
);

-- Example: { 
--   "number": 1234,
--   "comments": 20,
--   "reviews": [{ "id": "...", "status": "APPROVED" }],
--   "commits": [{ "oid": "...", "author": "..." }],
--   "ci_checks": [{ "name": "...", "status": "SUCCESS" }]
-- }
```

**Update efficiency:** 1 row update per PR per crawl (not N rows for N comments)

**Index strategy:** Use JSONB containment indexes only on critical fields
```sql
CREATE INDEX idx_pr_status ON repository_metadata USING gin(data -> 'reviews');
```

**Partitioning metadata by type:**
```sql
-- Store different metadata types separately for better performance
CREATE TABLE pr_metadata AS SELECT * FROM repository_metadata WHERE metadata_type = 'pr';
CREATE TABLE issue_metadata AS SELECT * FROM repository_metadata WHERE metadata_type = 'issue';
```

---

## Code Architecture Principles

1. **Anti-Corruption Layer** (`github_client.py`): Transform GitHub GraphQL response to domain model
2. **Separation of Concerns**: 
   - `fetcher.py` - orchestration only
   - `github_client.py` - API calls only
   - `repository.py` - database ops only
3. **Immutability:** Repositories passed as immutable dicts after fetch
4. **Rate Limit Isolation:** RateLimiter can be tested independently


## GitHub Actions

The pipeline:
1. Spins up PostgreSQL service container
2. Creates schema
3. Runs crawler for ~100K repos
4. Exports to CSV/JSON
5. Uploads artifacts

No private secrets required - uses default GitHub token.
