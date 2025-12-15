# Reddit Hate Speech Detection System

An automated system for collecting, enriching, and scoring Reddit posts and users for hate speech content.

For detailed system architecture, database schema, and technical documentation, see **[ARCHITECTURE.md](ARCHITECTURE.md)**.

## Quick Start

### Prerequisites

- **Docker** and **Docker Compose** (recommended)
- **Python 3.11+** and [uv](https://docs.astral.sh/uv/) (for local development)
- No Reddit API credentials required

### Run with Docker

```bash
# Start both API and scraper services
docker-compose up -d

# View logs
docker-compose logs -f
```

---

## Configuration

Copy the example environment file and customize as needed:

```bash
cp .env.example .env
```

### Key Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `TARGET_SUBREDDITS` | `news,politics,...` | Comma-separated subreddits to monitor |
| `POSTS_PER_SUBREDDIT` | `10` | Number of posts to collect per subreddit |
| `MAX_USERS_TO_ENRICH` | `20` | Maximum users to analyze per run |
| `USER_HISTORY_DAYS` | `60` | Days of user history to analyze |
| `CRITICAL_RISK_THRESHOLD` | `70` | Score threshold for critical risk level |
| `HIGH_RISK_THRESHOLD` | `50` | Score threshold for high risk level |
| `RATE_LIMIT_DELAY` | `2.0` | Seconds between Reddit requests |

### Service-Specific Configuration

Each service has its own `.env` file:
- `services/api/.env` - API service configuration
- `services/scraper/.env` - Scraper service configuration

---

## Running the Project

### Docker (Recommended)

```bash
# Start all services (API + continuous scraper)
docker-compose up -d

# API only (no scraper)
docker-compose up -d api

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Local Development

```bash
# API Service
cd services/api
uv sync
uv run uvicorn src.api:app --reload --host 0.0.0.0 --port 8000

# Scraper Service (in another terminal)
cd services/scraper
uv sync
uv run python -m src.main
```

---

## API Documentation (Swagger UI)

The API includes interactive documentation powered by **Swagger UI** and **ReDoc**:

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs | **Swagger UI** - Interactive API explorer with "Try it out" functionality |
| http://localhost:8000/redoc | **ReDoc** - Alternative API documentation with clean formatting |
| http://localhost:8000/health | Health check endpoint |
| http://localhost:8000/statistics | System statistics (post/user counts, risk distributions) |

### Using Swagger UI

1. Navigate to http://localhost:8000/docs
2. Browse available endpoints organized by category (Posts, Users, Alerts, Monitoring)
3. Click on any endpoint to expand it
4. Click **"Try it out"** to test the endpoint interactively
5. Fill in parameters and click **"Execute"** to see live responses

### Key API Endpoints

| Category | Endpoints |
|----------|-----------|
| **Posts** | `GET /posts`, `GET /posts/high-risk`, `POST /posts`, `PATCH /posts/{id}` |
| **Users** | `GET /users`, `GET /users/high-risk`, `GET /users/monitored`, `POST /users` |
| **Alerts** | `GET /alerts`, `POST /alerts`, `PATCH /alerts/{id}` |
| **Bulk** | `POST /bulk/posts`, `POST /bulk/users` |

---

## Testing

### Run All Tests

```bash
# API tests
cd services/api
uv run pytest -v

# Scraper tests
cd services/scraper
uv run pytest -v

# With coverage
uv run pytest --cov=src --cov-report=html
```

### Run Specific Tests

```bash
# Test specific module
uv run pytest tests/test_api.py -v

# Test specific function
uv run pytest tests/test_api.py::test_create_post -v

# Run with output
uv run pytest -v -s
```

---

## Exporting the Database

Export all database tables to CSV and JSON files:

### Using the Export Script

```bash
# Run the export script
python export_db.py
```

This exports all tables to `data/exports/`:
- `posts.csv` / `posts.json` - All collected posts with risk scores
- `users.csv` / `users.json` - All analyzed users with risk profiles
- `alerts.csv` / `alerts.json` - Generated alerts
- `monitoring_logs.csv` / `monitoring_logs.json` - Monitoring history

### Direct Database Access

The SQLite database is located at `data/reddit_detection.db`. You can query it directly:

```bash
# Open database
sqlite3 data/reddit_detection.db

# Example queries
sqlite> SELECT COUNT(*) FROM posts;
sqlite> SELECT * FROM users WHERE risk_level = 'critical';
sqlite> .tables
sqlite> .schema posts
```

---

## Project Structure

```
reddit-hatespeach-detector/
├── services/
│   ├── api/                 # FastAPI REST service
│   │   ├── src/
│   │   │   ├── api.py       # FastAPI application
│   │   │   └── database/    # SQLAlchemy models, CRUD, schemas
│   │   └── tests/           # API tests
│   │
│   └── scraper/             # Data collection & processing
│       ├── src/
│       │   ├── pipeline.py  # ETL pipeline
│       │   ├── collectors/  # Reddit data collection
│       │   ├── enrichers/   # User enrichment
│       │   └── scorers/     # Risk scoring (HurtLex)
│       └── tests/           # Scraper tests
│
├── data/
│   ├── reddit_detection.db  # SQLite database
│   ├── exports/             # Exported CSV/JSON files
│   └── hurtlex_processed.json
│
├── docker-compose.yml
├── export_db.py             # Database export script
├── ARCHITECTURE.md          # Detailed technical documentation
└── README.md
```

---

## Troubleshooting

### Logs

```bash
docker-compose logs -f api              # API logs
docker-compose logs -f scraper          # Scraper logs
docker-compose logs --tail=50           # Last 50 lines
```

### Common Issues

**Statistics showing zeros**: Wait for scraper to complete (2-5 minutes) or check logs:
```bash
docker-compose logs scraper | grep -i "pipeline"
```

**Database not found**: Ensure the `data/` directory exists and is mounted correctly.

**Rate limiting**: Increase `RATE_LIMIT_DELAY` in `.env` if getting blocked by Reddit.

---

## License

MIT License
