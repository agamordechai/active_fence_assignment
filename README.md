# Reddit Hate Speech Detection System

An automated system for collecting, enriching, and scoring Reddit posts and users for violent hate speech content.

## Features

- 🔍 **Data Collection**: Automated Reddit post and user data collection using PRAW
- 📊 **Data Enrichment**: Comprehensive user history analysis (2+ months)
- 🎯 **Risk Scoring**: ML-based hate speech and violence detection
- 📈 **Monitoring**: Daily monitoring of flagged users with alerts
- 🐳 **Docker Support**: Fully containerized with Docker Compose
- 📦 **Modern Python**: Uses UV and Poetry for dependency management

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Reddit API credentials ([get them here](https://www.reddit.com/prefs/apps))

### Setup

1. **Clone and configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Reddit API credentials
   ```

2. **Build and run with Docker**:
   ```bash
   docker-compose up --build
   ```

### Local Development (without Docker)

1. **Install UV** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install Poetry** (if not already installed):
   ```bash
   pip install poetry
   ```

3. **Install dependencies**:
   ```bash
   poetry install
   ```

4. **Run the application**:
   ```bash
   poetry run python -m src.main
   ```

## Project Structure

```
reddit-hate-speech-detector/
├── src/
│   ├── collectors/          # Reddit data collection
│   ├── enrichers/           # User history enrichment
│   ├── scorers/             # Risk scoring algorithms
│   ├── monitors/            # Daily monitoring system
│   └── utils/               # Utilities and helpers
├── tests/                   # Test suite
├── data/                    # Data output (gitignored)
│   ├── raw/                 # Raw collected data
│   └── processed/           # Processed and scored data
├── logs/                    # Application logs
├── config/                  # Configuration files
├── Dockerfile               # Docker container definition
├── docker-compose.yml       # Docker Compose configuration
└── pyproject.toml          # Python dependencies and config

```

## Configuration

Edit `.env` file to configure:

- **Reddit API credentials**
- **Collection parameters** (max posts, date ranges)
- **Risk thresholds**
- **Monitoring settings**

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

