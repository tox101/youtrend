import sys
import os
import logging
import platform
import asyncio

# Fix Windows asyncio NotImplementedError for Playwright subprocesses
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time

# Adjust python path to load roots properly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from api.router import api_router

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
)
logger = logging.getLogger("backend.main")

from contextlib import asynccontextmanager
import asyncio
from database.connection import init_timescaledb, AsyncSessionLocal
from sqlalchemy import func, select
from models.rank import VideoRank
from crawler.collector import DataCollector
from ranking.engine import RankingEngine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize database configurations and TimescaleDB extension/hypertables
    logger.info("Initializing TimescaleDB configurations...")
    await init_timescaledb()
    
    # 2. Check for empty database and auto-run pipeline to prevent empty frontend charts (Cold Start protection)
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count(VideoRank.id)))
        rank_count = result.scalar()
        
    if rank_count == 0:
        logger.info("Database is empty. Automatically launching initial data ingestion & ranking compute...")
        
        async def run_initial_pipeline():
            try:
                # Run crawler
                collector = DataCollector()
                await collector.run_pipeline()
                logger.info("Initial crawl step finished.")
                
                # Run ranking compute
                async with AsyncSessionLocal() as rank_session:
                    engine = RankingEngine(rank_session)
                    await engine.run_global_pipeline()
                    await rank_session.commit()
                logger.info("Initial ranking calculation finished. Ready.")
            except Exception as ex:
                logger.error(f"Failed to execute initial auto-ingestion pipeline: {ex}", exc_info=True)

        # Run immediately in non-blocking background loop to avoid slowing down API start
        asyncio.create_task(run_initial_pipeline())
    else:
        logger.info(f"Database ranks table has {rank_count} records. Skipping initial auto-run.")
        
    yield

app = FastAPI(
    title="YouTube Global Intelligence Platform API",
    description="Backend services for analyzing YouTube trending algorithms, virality score, and radar indicators globally.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# CORS Configuration for Next.js Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to actual frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Middleware for request metrics and JSON logger
class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        
        logger.info(
            f"HTTP Request: method={request.method} path={request.url.path} status_code={response.status_code} duration={process_time:.2f}ms"
        )
        return response

app.add_middleware(StructuredLoggingMiddleware)

@app.get("/", tags=["Health Check"])
async def root():
    return {
        "status": "healthy",
        "service": "YouTube Global Intelligence Platform API",
        "timestamp": time.time()
    }

# Register major APIRouter
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    # Start the server locally with explicit asyncio loop to preserve selector loop policy
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True, loop="asyncio")

