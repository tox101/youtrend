import asyncio
import platform
import logging
import sys
import os

# Fix Windows asyncio NotImplementedError for Playwright subprocesses
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


# Adjust python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import AsyncSessionLocal
from crawler.collector import DataCollector
from ranking.engine import RankingEngine

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
)
logger = logging.getLogger("scheduler.tasks")

async def run_pipeline_step():
    """
    Executes one iteration of the data pipeline:
    1. Run Crawler -> 2. Ingest Data -> 3. Run Ranking Engine.
    """
    logger.info("Scheduler Triggered: Initiating crawling pipeline...")
    collector = DataCollector()
    
    # 1 & 2. Crawl and Ingest Data
    try:
        await collector.run_pipeline()
        logger.info("Crawling and ingestion completed successfully.")
    except Exception as e:
        logger.error(f"Error during crawling pipeline step: {e}", exc_info=True)

    # 3. Compute Rankings
    logger.info("Initiating ranking calculation engine...")
    async with AsyncSessionLocal() as session:
        engine = RankingEngine(session)
        try:
            await engine.run_global_pipeline()
            await session.commit()
            logger.info("Ranking calculations and database updates completed successfully.")
        except Exception as e:
            logger.error(f"Error during ranking engine step: {e}", exc_info=True)
            await session.rollback()

async def main():
    logger.info("Starting background scheduler daemon. Interval: 5 minutes (300s).")
    # Run immediately on startup
    await run_pipeline_step()
    
    while True:
        try:
            # Wait for 5 minutes
            await asyncio.sleep(300)
            await run_pipeline_step()
        except asyncio.CancelledError:
            logger.info("Scheduler daemon received cancel signal. Shutting down.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in scheduler loop: {e}", exc_info=True)
            # Sleep brief period before retrying loop to prevent hot loop spin on failure
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
