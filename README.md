# Reddit Hate Speech Detection System

An automated system for collecting, enriching, and scoring Reddit posts and users for violent hate speech content.

## Features

- 🔍 **Data Collection**: Automated Reddit post and user data collection using web scraping
- 📊 **Data Enrichment**: Comprehensive user history analysis (2+ months)
- 🎯 **Risk Scoring**: Rule-based hate speech and violence detection
- 🗄️ **Database & API**: SQLite database with FastAPI REST API (30+ endpoints)
- 📚 **Interactive Docs**: Auto-generated API documentation with Swagger UI
- 🐳 **Docker Support**: Fully containerized with Docker Compose
- 📦 **Modern Python**: Uses Poetry for dependency management

## Note on Data Collection

Due to Reddit's recent API policy changes requiring approval for API access, this project uses Reddit's public JSON endpoints for data collection. This approach:
- ✅ Requires **no API credentials** or approval process
- ✅ Works with **public data** only
- ✅ Respects Reddit's rate limits with built-in delays
- ✅ Suitable for **research and educational purposes**
- ⚠️ Limited to public posts and user data

## Quick Start

### Prerequisites

- Docker and Docker Compose OR Python 3.11+
- No Reddit API credentials needed!

### Setup (Docker - Recommended)

1. **Start services**:
   ```bash
   docker-compose up
   ```
   
   This starts:
   - ✅ Data collection service (collects, scores, and **auto-imports to database**)
   - ✅ REST API on port 8000 (also auto-imports data on startup)

2. **Access the API**:
   - Interactive Docs: http://localhost:8000/docs
   - API Statistics: http://localhost:8000/statistics
   - Health Check: http://localhost:8000/health

3. **View logs**:
   ```bash
   # View API logs
   docker-compose logs -f api
   
   # View scraper logs (watch data collection + auto-import)
   docker-compose logs -f reddit-scraper
   
   # View all logs
   docker-compose logs -f
   
   # View last 50 lines
   docker-compose logs --tail=50 api
   ```

4. **Change log verbosity** (if needed):
   ```bash
   # Edit .env and change LOG_LEVEL:
   # LOG_LEVEL=WARNING  # Default (less verbose, only warnings/errors)
   # LOG_LEVEL=INFO     # More verbose (shows all pipeline steps)
   # LOG_LEVEL=DEBUG    # Most verbose (detailed debugging info)
   
   # Then restart:
   docker-compose restart
   ```

**Note:** Data is automatically imported to the database in TWO ways:
- ✅ **After scraper completes** - Pipeline automatically imports collected data
- ✅ **When API starts** - API imports any existing data files on startup

### Verifying Auto-Import is Working

After starting the services, the auto-import should happen automatically. Here's how to verify:

**1. Watch for auto-import messages (takes 3-5 minutes):**
```bash
docker-compose logs -f reddit-scraper

# You should see:
# ================================================================================
# [AUTO-IMPORT] Importing data to database...
# ================================================================================
#   ✓ Database initialized
#   📥 Importing posts from data/processed/posts_scored_*.json...
#   ✓ Posts: 125 created, 0 skipped
#   📥 Importing users from data/processed/users_scored_*.json...
#   ✓ Users: 20 created, 0 skipped
# ================================================================================
# ✅ DATABASE IMPORT COMPLETED!
# ================================================================================
```

**2. Check database was populated:**
```bash
curl http://localhost:8000/statistics

# Should show real numbers:
# {"total_posts": 125, "total_users": 20, ...}
```

**3. If auto-import didn't run:**
```bash
# Rebuild with latest code
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Or manually import
python3 manual_import.py
```

## Troubleshooting

### Viewing Logs While Containers are Running

```bash
# Follow logs in real-time
docker-compose logs -f api                    # API only
docker-compose logs -f reddit-scraper         # Scraper only
docker-compose logs -f                        # All services

# View last N lines
docker-compose logs --tail=100 api            # Last 100 lines
docker-compose logs --tail=50 reddit-scraper  # Last 50 lines

# Search logs
docker-compose logs api | grep "import"       # Search for "import"
docker-compose logs api | grep -i "error"     # Search for errors
```

### Changing Log Verbosity

**Current default: `WARNING`** (minimal output, only warnings and errors)

To see more details:

1. **Edit `.env` file**:
   ```bash
   LOG_LEVEL=INFO     # Shows pipeline steps, imports, etc.
   # or
   LOG_LEVEL=DEBUG    # Shows everything (very verbose)
   ```

2. **Restart containers**:
   ```bash
   docker-compose restart
   ```

3. **Or set temporarily**:
   ```bash
   LOG_LEVEL=INFO docker-compose up
   ```

### Docker Container Error (entrypoint.sh mount error)

If you see an error about `docker-entrypoint.sh`, old containers are stuck. Fix:

```bash
# Complete reset
./restart.sh

# Or manually:
docker-compose down -v
docker rm -f reddit-api reddit-scraper
docker-compose up -d
```

### Statistics Showing All Zeros

If `http://localhost:8000/statistics` shows all zeros, the database is empty. Try these solutions:

**Solution 1: Complete restart (RECOMMENDED)**
```bash
./restart.sh
# Wait 30 seconds, then check http://localhost:8000/statistics
```

**Solution 2: Manual import from host**
```bash
python3 manual_import.py
```

**Solution 3: Check if data was collected**
```bash
ls -lh data/processed/  # Should see posts_scored_*.json files
```

If no data files exist, the scraper hasn't run yet. Let it complete (takes 2-5 minutes):
```bash
docker-compose logs -f reddit-scraper  # Watch it collect data
```

### Still Empty After 10 Minutes?

The auto-import on startup might have failed. Check logs:
```bash
# Check if import ran
docker-compose logs api | grep -i "import"

# Should see:
# "Auto-importing latest data..."
# "Data import completed"

# If not, manually import:
docker-compose exec api python -m src.import_data
```

### Local Development (without Docker)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the data collection**:
   ```bash
   python -m src.main
   ```

3. **Start the API server**:
   ```bash
   uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
   ```
   Access at: http://localhost:8000/docs

4. **Import data into database**:
   ```bash
   python -m src.import_data
   ```

## API & Database

This project includes a complete REST API with database storage.

### Docker (Recommended)
```bash
docker-compose up        # Starts API + Scraper
```
Access at: http://localhost:8000/docs

### Local
```bash
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

**Key Features:**
- 30+ REST endpoints for posts, users, and data management
- Interactive Docs: http://localhost:8000/docs
- Import Data: `docker-compose exec api python -m src.import_data` (Docker) or `python -m src.import_data` (Local)
- Advanced filtering and querying
- Risk assessment integration
- Bulk import capabilities
- Auto-generated documentation

## Project Structure

```
reddit-hate-speech-detector/
├── src/
│   ├── collectors/          # Reddit data collection
│   ├── enrichers/           # User history enrichment
│   ├── scorers/             # Risk scoring algorithms
│   ├── database/            # Database models and API
│   │   ├── models.py        # SQLAlchemy ORM models
│   │   ├── database.py      # Database connection
│   │   ├── crud.py          # CRUD operations
│   │   └── schemas.py       # Pydantic schemas
│   ├── api.py               # FastAPI application
│   ├── import_data.py       # Data import utility
│   └── utils/               # Utilities and helpers
├── tests/                   # Test suite
├── data/                    # Data output (gitignored)
│   ├── raw/                 # Raw collected data
│   ├── processed/           # Processed and scored data
│   └── reddit_detection.db  # SQLite database
├── logs/                    # Application logs
├── config/                  # Configuration files
├── Dockerfile               # Docker container definition
├── docker-compose.yml       # Docker Compose configuration
├── requirements.txt         # Python dependencies
└── pyproject.toml           # Project metadata
```

## Configuration

Edit `.env` file to configure:

- **Target subreddits** (comma-separated, no 'r/' prefix):
  ```dotenv
  TARGET_SUBREDDITS=news,politics,AskReddit,worldnews
  ```
- **Collection parameters**:
  ```dotenv
  POSTS_PER_SUBREDDIT=25        # Posts per subreddit
  MAX_USERS_TO_ENRICH=20        # Users to analyze
  ```
- **Risk thresholds**:
  ```dotenv
  CRITICAL_RISK_THRESHOLD=70
  HIGH_RISK_THRESHOLD=50
  ```

**Example:** To change which subreddits to monitor:
```bash
# Edit .env file:
TARGET_SUBREDDITS=news,worldnews,politics,conspiracy,unpopularopinion

# Then restart:
docker-compose restart reddit-scraper
```

## Docker Commands

```bash
# Build and start services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up --build --force-recreate
```

## Development

### Code Quality

```bash
# Format code
poetry run black src/ tests/

# Lint code
poetry run ruff src/ tests/

# Type checking
poetry run mypy src/

# Run tests
poetry run pytest
```

### Using UV

```bash
# Install with UV
uv pip install -r requirements.txt

# Add a package
uv pip install package-name
```

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/test_collectors.py
```

## Data Output

- **Raw data**: `data/raw/posts.json`, `data/raw/users.json`
- **Processed data**: `data/processed/scored_posts.csv`, `data/processed/flagged_users.csv`
- **Logs**: `logs/app.log`

## License

MIT License

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

