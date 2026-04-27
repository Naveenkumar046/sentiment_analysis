# Architecture Overview

## System Design

The application follows a layered architecture pattern optimized for production workloads.

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Web Layer                    │
│                  (app/main.py)                          │
└────────┬────────────────────────────────────────────┬───┘
         │                                            │
         │                                            │
    ┌────▼──────────────────────────┐    ┌──────────▼────────────┐
    │     API Route Layer            │    │  Middleware Layer    │
    │   (app/api/endpoints.py)       │    │  (CORS, Logging,     │
    │                                │    │   Health Checks)     │
    │  • Request handling            │    │                      │
    │  • Response formatting         │    │                      │
    │  • Error handling              │    │                      │
    │  • Input validation            │    │                      │
    └────┬──────────────────────────┘    └──────────┬───────────┘
         │                                           │
         │                                           │
    ┌────▼──────────────────────────────────────────▼────┐
    │           Business Logic Layer                     │
    │                                                    │
    │  ┌──────────────────┐  ┌────────────────────┐    │
    │  │  NLP Engine      │  │  Amazon Scraper    │    │
    │  │  (nlp_engine.py) │  │  (scraper.py)      │    │
    │  │                  │  │                    │    │
    │  │ • Sentiment      │  │ • Web scraping     │    │
    │  │   analysis       │  │ • Data extraction  │    │
    │  │ • Keyword        │  │ • Error recovery   │    │
    │  │   extraction     │  │                    │    │
    │  └──────────────────┘  └────────────────────┘    │
    └────┬──────────────────────────────────────────┬───┘
         │                                          │
         │                                          │
    ┌────▼──────────────────────────┐ ┌───────────▼──────────────┐
    │    Data Access Layer          │ │  Configuration Layer     │
    │  (database/session.py)        │ │  (config.py)             │
    │                               │ │                          │
    │  • Session management         │ │  • Environment loading   │
    │  • Connection pooling         │ │  • Settings validation   │
    │  • Query execution            │ │  • Secrets management    │
    │  • Transaction handling       │ │                          │
    └────┬──────────────────────────┘ └──────────────────────────┘
         │
         │
    ┌────▼───────────────────────────┐
    │      Data Models               │
    │  (database/models.py)          │
    │                                │
    │  • Review                      │
    │  • Product metadata            │
    └────┬───────────────────────────┘
         │
         │
    ┌────▼───────────────────────────┐
    │        Database                │
    │  (SQLite/PostgreSQL/MySQL)     │
    │                                │
    │  • Reviews table               │
    │  • Sentiment data              │
    │  • Product variants            │
    └────────────────────────────────┘
```

## Component Overview

### 1. Web Layer (FastAPI)

**File**: `app/main.py`

- **Responsibility**: HTTP request/response handling
- **Features**:
  - Application lifecycle management (startup/shutdown)
  - CORS middleware configuration
  - Global exception handling
  - Health check endpoint
  - API versioning support

### 2. API Routes Layer

**File**: `app/api/endpoints.py`

- **Responsibility**: HTTP endpoint implementation
- **Endpoints**:
  - `/` - Health check
  - `/api/v1/analyze-sentiment` - Single review analysis
  - `/api/v1/ingest` - Batch scraping and storage
  - `/api/v1/reviews` - Retrieve with filtering
  - `/api/v1/keywords` - Keyword extraction
- **Features**:
  - Request validation with Pydantic
  - Response formatting
  - Error handling with proper status codes
  - Pagination support

### 3. Business Logic Layer

**Components**:

#### 3.1 NLP Engine
**File**: `app/sentiment_analysis/nlp_engine.py`

- Uses DistilBERT transformer model
- Sentiment classification (POSITIVE/NEGATIVE)
- Confidence scoring
- Keyword extraction using TF-IDF
- Error handling and logging

#### 3.2 Web Scraper
**File**: `app/services/scraper.py`

- Amazon product page scraping
- HTML parsing with BeautifulSoup
- Variant extraction (color, storage)
- Retry logic for resilience
- Error recovery

### 4. Data Access Layer

**File**: `app/database/session.py`

- **Responsibility**: Database connectivity
- **Features**:
  - SQLAlchemy session factory
  - Connection pooling
  - Dependency injection support
  - Error handling
  - Database initialization

**File**: `app/database/models.py`

- **Responsibility**: Data models
- **Models**:
  - Review model with all metadata
  - Relationships and constraints

### 5. Data Validation Layer

**File**: `app/schemas/review.py`

- Pydantic models for validation
- Request/response schemas
- Field constraints and validation
- Example data for documentation

### 6. Configuration Layer

**File**: `app/config.py`

- **Responsibility**: Application configuration
- **Features**:
  - Environment variable loading
  - Settings validation
  - Lazy initialization
  - Singleton pattern

## Data Flow

### Review Ingestion Flow

```
1. User POST /api/v1/ingest?url=...
   ↓
2. Endpoint receives request
   ↓
3. Validate URL format
   ↓
4. Call Scraper.scrape(url)
   ├─ Fetch page with retry logic
   ├─ Parse HTML
   └─ Extract review data
   ↓
5. For each review:
   ├─ Call NLPEngine.get_sentiment()
   ├─ Analyze sentiment with DistilBERT
   └─ Store in database with sentiment score
   ↓
6. Return success response with count
```

### Sentiment Analysis Flow

```
1. User POST /api/v1/analyze-sentiment
   ↓
2. Endpoint receives and validates request
   ↓
3. Extract review text
   ↓
4. Call NLPEngine.get_sentiment(text)
   ├─ Truncate to 512 tokens
   ├─ Run through DistilBERT
   └─ Extract label and score
   ↓
5. Format and return response
```

### Review Retrieval Flow

```
1. User GET /api/v1/reviews?filters...
   ↓
2. Endpoint receives request
   ↓
3. Build database query with filters
   ├─ Optional: color filter
   ├─ Optional: storage filter
   ├─ Optional: rating filter
   ├─ Optional: sentiment filter
   └─ Optional: pagination
   ↓
4. Execute query
   ↓
5. Format results with Pydantic
   ↓
6. Return paginated response
```

## Request/Response Cycle

### HTTP Request

```
POST /api/v1/analyze-sentiment
Content-Type: application/json

{
  "title": "Great product",
  "text": "This product is excellent and works as advertised.",
  "rating": 5
}
```

### Validation (Pydantic)

```python
ReviewCreate(
    title="Great product",
    text="This product is excellent...",
    rating=5
)
```

### Processing

```python
sentiment, score = nlp_engine.get_sentiment(text)
# sentiment = "POSITIVE"
# score = 0.99
```

### Response

```json
{
  "text": "This product is excellent and works as advertised.",
  "sentiment": "POSITIVE",
  "confidence": 0.99
}
```

## Error Handling

### Levels

1. **Input Validation** (400 Bad Request)
   - Pydantic schema validation
   - Field constraints

2. **Business Logic** (422 Unprocessable Entity)
   - Invalid Amazon URL
   - No reviews found
   - Model errors

3. **Database** (500 Internal Server Error)
   - Connection failures
   - Query errors
   - Transaction rollback

4. **Server** (500 Internal Server Error)
   - Unexpected exceptions
   - Logging and monitoring

### Error Response

```json
{
  "detail": "Descriptive error message"
}
```

## Security Architecture

```
┌─────────────────────────────────────┐
│      Input Validation Layer         │
│  (Pydantic + Field Constraints)     │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│    Authentication/Authorization     │
│     (Future: OAuth2/JWT support)    │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│     Business Logic Layer            │
│  (Sanitize + Validate Data)         │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│    Database Layer (ORM)             │
│ (Prevent SQL Injection)             │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│       Persistent Storage            │
└─────────────────────────────────────┘
```

## Deployment Architecture

### Docker Container Architecture

```
┌─────────────────────────────────────┐
│        Docker Container             │
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐   │
│  │   Uvicorn/Gunicorn         │   │
│  │   - 4 Worker Processes     │   │
│  │   - Listen on :8000        │   │
│  └──────────┬──────────────────┘   │
│             │                       │
│  ┌──────────▼──────────────────┐   │
│  │   FastAPI Application       │   │
│  │   - API Routes              │   │
│  │   - Business Logic          │   │
│  │   - NLP Engine              │   │
│  │   - Scraper Service         │   │
│  └──────────┬──────────────────┘   │
│             │                       │
│  ┌──────────▼──────────────────┐   │
│  │   SQLAlchemy ORM            │   │
│  │   - Session Management      │   │
│  │   - Connection Pooling      │   │
│  └──────────┬──────────────────┘   │
│             │                       │
│             │ (Volume Mount)        │
└─────────────┼──────────────────────┘
              │
    ┌─────────▼─────────┐
    │   SQLite DB File  │
    │  (or PostgreSQL)  │
    └───────────────────┘
```

## Performance Optimization

### Database Optimization

- Connection pooling
- Index on frequently filtered columns
- Prepared statements
- Query optimization

### Application Optimization

- Lazy model loading
- Efficient pagination
- Caching ready (future)
- Worker process scaling

### Infrastructure Optimization

- Container orchestration (Kubernetes)
- Load balancing (nginx)
- Horizontal scaling
- Resource limits

## Monitoring and Observability

### Logging Strategy

```
Level       Usage
─────────────────────────────────
DEBUG       Development only
INFO        Normal operations
WARNING     Degraded service
ERROR       Service failures
```

### Metrics to Monitor

- API response times
- Error rates
- Database connection pool usage
- Memory consumption
- CPU utilization
- Active requests

### Health Checks

- Application health: `GET /`
- Database connectivity
- Model availability
- Disk space

## Testing Strategy

### Test Coverage

- Unit tests (endpoints, services)
- Integration tests (database, API)
- Functional tests (complete workflows)

### Test Pyramid

```
        △
       /|\
      / | \  Integration Tests
     /  |  \
    /   |   \
   ───────── 
  /    |    \  Unit Tests
 /     |     \
───────────────
```

## Deployment Strategy

### Local Development

- Virtual environment
- SQLite database
- Reload on file changes

### Production

- Docker Compose (single server)
- Kubernetes (multi-server)
- PostgreSQL database
- Gunicorn + Nginx
- Load balancing
- Auto-scaling

---

**This architecture ensures scalability, maintainability, and production-readiness.**
