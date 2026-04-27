"""Database session and connection management."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from config import get_settings
import logging

logger = logging.getLogger(__name__)

settings = get_settings()

# Create database engine with proper configuration
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    poolclass=NullPool if "sqlite" in settings.DATABASE_URL else None,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


from starlette.exceptions import HTTPException as StarletteHTTPException

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    except StarletteHTTPException:
        # This is a normal API error (like 422), just re-raise it
        raise
    except Exception as e:
        # This is a REAL database or code error, log it
        logger.exception("Actual Database/System error")
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    from database.models import Base
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
