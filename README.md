# Amazon Sentiment Analysis Pro

Enterprise-grade sentiment analysis application for Amazon product reviews using FastAPI, SQLAlchemy, and DistilBERT transformer models.

## Features

- **Web Scraping**: Extract product reviews directly from Amazon product pages
- **Sentiment Analysis**: Analyze sentiment using DistilBERT NLP model
- **REST API**: Modern FastAPI endpoints with full documentation
- **Database**: SQLAlchemy ORM with SQLite support (configurable for production databases)
- **Error Handling**: Comprehensive error handling and logging
- **Production Ready**: Docker support, environment configuration, health checks
- **Type Safety**: Full type hints with Pydantic validation

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints.py        # API route handlers
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py           # SQLAlchemy models
│   │   └── session.py          # Database session management
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── review.py           # Pydantic schemas
│   ├── sentiment_analysis/
│   │   ├── __init__.py
│   │   └── nlp_engine.py       # NLP sentiment analysis
│   └── services/
│       ├── __init__.py
│       └── scraper.py          # Amazon scraper service
├── Dockerfile                  # Multi-stage Docker build
├── docker-compose.yml          # Docker Compose configuration
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
└── README.md                   # This file
```

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (for containerized deployment)
- 4GB+ RAM (for transformer models)

## Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Enterprise_bot_sentiment_analysis
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file**
   ```bash
   cp .env.example .env
   ```

5. **Run application**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Check application status**
   ```bash
   docker-compose logs -f app
   ```

3. **Stop application**
   ```bash
   docker-compose down
   ```

## API Documentation

Once the application is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints

#### Health Check
- **GET** `/` - Application health status

#### Sentiment Analysis
- **POST** `/api/v1/analyze-sentiment` - Analyze sentiment of single review
  ```json
  {
    "title": "Great product",
    "text": "This product is excellent and works as advertised.",
    "rating": 5
  }
  ```

#### Data Ingestion
- **POST** `/api/v1/ingest` - Scrape and store reviews from Amazon URL
  ```
  POST /api/v1/ingest?url=https://www.amazon.com/product-reviews/...
  ```

#### Review Retrieval
- **GET** `/api/v1/reviews` - Retrieve reviews with filtering
  ```
  GET /api/v1/reviews?color=Black&storage=128GB&sentiment=POSITIVE&limit=50
  ```

#### Keyword Extraction
- **GET** `/api/v1/keywords` - Extract keywords from positive/negative reviews
  ```
  GET /api/v1/keywords?top_n=10
  ```

## Configuration

Create a `.env` file based on `.env.example`:

```env
# API Configuration
API_TITLE=Amazon Sentiment Analysis Pro
API_VERSION=1.0.0
DEBUG=false

# Database Configuration
DATABASE_URL=sqlite:///./sentiment_analysis.db
DATABASE_ECHO=false

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4

# NLP Configuration
NLP_MODEL=distilbert-base-uncased-finetuned-sst-2-english
USE_GPU=false

# Logging Configuration
LOG_LEVEL=INFO
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `DATABASE_URL` | `sqlite:///./sentiment_analysis.db` | Database connection string |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `USE_GPU` | `false` | Enable GPU for transformer models |

## Database

### Models

#### Review
- `id`: Primary key
- `title`: Review title
- `text`: Review text
- `rating`: Product rating (1-5)
- `storage`: Product storage variant
- `color`: Product color variant
- `verified`: Verified purchase flag
- `sentiment`: Analyzed sentiment (POSITIVE/NEGATIVE)
- `sentiment_score`: Confidence score (0.0-1.0)

### Database Migration

For production PostgreSQL/MySQL, create migrations:

```bash
alembic init migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Development

### Code Quality

```bash
# Format code
black app/

# Sort imports
isort app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

### Testing

```bash
pytest tests/ -v
pytest tests/ --cov=app
```

### Running Locally with Reload

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Production Deployment

### With Gunicorn

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 app.main:app
```

### With Docker

```bash
# Build image
docker build -t sentiment-analysis:latest .

# Run container
docker run -d \
  --name sentiment-api \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@db:5432/sentiment \
  sentiment-analysis:latest
```

### Performance Optimization

- Use PostgreSQL for production databases
- Enable GPU support by setting `USE_GPU=true` in `.env`
- Scale horizontally using multiple worker processes
- Use a reverse proxy (nginx) for load balancing
- Implement caching for frequently accessed data

## Troubleshooting

### Models Not Downloading

The first run will download transformer models (~500MB). Ensure you have:
- Stable internet connection
- Sufficient disk space
- Access to Hugging Face model hub

### Database Locked Error

SQLite has concurrency limitations. For production:
```bash
# Use PostgreSQL instead
DATABASE_URL=postgresql://user:password@localhost/sentiment_analysis
```

### Memory Issues

Reduce model size or enable GPU:
```env
NLP_MODEL=distilbert-base-uncased-finetuned-sst-2-english
USE_GPU=true
```

## Security Considerations

- Never commit `.env` files to version control
- Use strong database credentials in production
- Enable CORS only for trusted domains in production
- Keep dependencies updated regularly
- Use non-root user in Docker containers
- Validate all input data

## Performance Metrics

- Sentiment Analysis: ~200ms per review (CPU), ~50ms (GPU)
- Web Scraping: ~2-5 seconds per page
- Database Queries: <100ms for filtered results

## License

Proprietary - All rights reserved

## Support

For issues, feature requests, or improvements, please open an issue or contact the development team.
