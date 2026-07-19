import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environmental variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "youtube_global_intel")

# Read overriding DATABASE_URL if set (e.g. sqlite+aiosqlite:///./youtube.db)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    ASYNC_DATABASE_URL = DATABASE_URL
    # For sync connections (alembic, seed), map async driver name back to sync equivalent
    SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg", "postgresql").replace("sqlite+aiosqlite", "sqlite")
else:
    # Default PostgreSQL Connection Strings
    SYNC_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    ASYNC_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Engines configuration based on dialect
is_sqlite = "sqlite" in ASYNC_DATABASE_URL

if is_sqlite:
    sync_engine = create_engine(
        SYNC_DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in SYNC_DATABASE_URL else {}
    )
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    sync_engine = create_engine(
        SYNC_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )


# Session Factories
SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# Dependency for FastAPI
async def get_db() -> AsyncSession:
    """
    FastAPI Dependency to get asynchronous DB Session.
    Ensures session is closed after request lifecycle.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_timescaledb() -> None:
    """
    Checks if database runs on PostgreSQL and initializes TimescaleDB extension
    and converts the 'ranking_history' table to a Hypertable.
    """
    from sqlalchemy import text
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Check dialect
            bind = session.bind
            if bind and "postgresql" in bind.dialect.name:
                try:
                    # Enable TimescaleDB Extension if exists
                    await session.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
                    
                    # Convert table to Hypertable for optimized time-series compression
                    await session.execute(text(
                        "SELECT create_hypertable('ranking_history', 'recorded_at', if_not_exists => TRUE);"
                    ))
                    print("TimescaleDB extension enabled and ranking_history converted to Hypertable.")
                except Exception as e:
                    # Fail silently or log if TimescaleDB extension package is not installed on the PG image
                    print(f"Skipping TimescaleDB setup: {e}. Running on standard PostgreSQL.")

