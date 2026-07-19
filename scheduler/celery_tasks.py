"""
Celery Task Definitions for YouTube Global Intelligence Platform.

These tasks replace the monolithic scheduler loop with isolated,
horizontally-scalable Celery workers.

Usage:
  # Start Celery worker
  celery -A scheduler.celery_app worker --loglevel=info

  # Start Celery Beat scheduler (triggers tasks on interval)
  celery -A scheduler.celery_app beat --loglevel=info
"""

import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scheduler.celery_app import app
from database.connection import AsyncSessionLocal

logger = logging.getLogger("scheduler.celery_tasks")


def _run_async(coro):
    """Helper to run an async coroutine inside a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.task(name="scheduler.celery_tasks.run_crawl_pipeline")
def run_crawl_pipeline():
    """
    Celery Task 1: Execute the YouTube data collection pipeline.
    Crawls all 8 countries using API + Playwright fallback.
    """
    logger.info("[Celery Worker] Starting crawl pipeline task...")

    async def _crawl():
        from crawler.collector import DataCollector
        collector = DataCollector()
        await collector.run_pipeline()
        logger.info("[Celery Worker] Crawl pipeline completed.")

    _run_async(_crawl())
    return {"status": "crawl_complete"}


@app.task(name="scheduler.celery_tasks.run_ranking_pipeline")
def run_ranking_pipeline():
    """
    Celery Task 2: Execute the Virality Score computation and ranking engine.
    """
    logger.info("[Celery Worker] Starting ranking engine task...")

    async def _rank():
        async with AsyncSessionLocal() as session:
            from ranking.engine import RankingEngine
            engine = RankingEngine(session)
            await engine.run_global_pipeline()
            await session.commit()
        logger.info("[Celery Worker] Ranking engine completed.")

    _run_async(_rank())
    return {"status": "ranking_complete"}


@app.task(name="scheduler.celery_tasks.run_full_pipeline")
def run_full_pipeline():
    """
    Celery Task 3 (Composite): Runs Crawl → Rank in sequence.
    Triggered by Celery Beat every 5 minutes.
    """
    logger.info("[Celery Beat] Full pipeline triggered. Step 1: Crawl, Step 2: Rank.")

    # Step 1: Crawl
    try:
        run_crawl_pipeline()
    except Exception as e:
        logger.error(f"[Celery Beat] Crawl step failed: {e}", exc_info=True)

    # Step 2: Rank
    try:
        run_ranking_pipeline()
    except Exception as e:
        logger.error(f"[Celery Beat] Ranking step failed: {e}", exc_info=True)

    logger.info("[Celery Beat] Full pipeline finished.")
    return {"status": "full_pipeline_complete"}
