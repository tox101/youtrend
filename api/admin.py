import logging
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db, AsyncSessionLocal
from crawler.collector import DataCollector
from ranking.engine import RankingEngine

router = APIRouter(prefix="/admin", tags=["System Admin"])
logger = logging.getLogger("api.admin")

async def background_crawl_task():
    """Executes the crawler data collector pipeline in the background."""
    logger.info("Web Trigger: Starting background crawler pipeline...")
    try:
        collector = DataCollector()
        await collector.run_pipeline()
        logger.info("Web Trigger: Background crawler pipeline finished.")
    except Exception as e:
        logger.error(f"Web Trigger: Background crawler pipeline failed: {e}", exc_info=True)


async def background_ranking_task():
    """Executes the ranking engine pipeline in the background."""
    logger.info("Web Trigger: Starting background ranking engine...")
    try:
        async with AsyncSessionLocal() as session:
            engine = RankingEngine(session)
            await engine.run_global_pipeline()
            await session.commit()
        logger.info("Web Trigger: Background ranking engine finished.")
    except Exception as e:
        logger.error(f"Web Trigger: Background ranking engine failed: {e}", exc_info=True)


@router.post("/run-crawler")
async def trigger_crawler(background_tasks: BackgroundTasks):
    """
    Triggers the YouTube crawler immediately in a non-blocking background task.
    """
    background_tasks.add_task(background_crawl_task)
    return {
        "status": "success",
        "message": "크롤러 파이프라인 가동을 백그라운드 태스크로 시작했습니다. 수집 로그는 백엔드 콘솔에서 확인 가능합니다."
    }


@router.post("/run-ranking")
async def trigger_ranking_engine(background_tasks: BackgroundTasks):
    """
    Triggers the Virality Score ranking compute engine immediately in a non-blocking background task.
    """
    background_tasks.add_task(background_ranking_task)
    return {
        "status": "success",
        "message": "랭킹 엔진 재연산을 백그라운드 태스크로 시작했습니다. 결과는 잠시 후 반영됩니다."
    }


from models.video import Video
from models.channel import Channel
from models.rank import VideoRank
from sqlalchemy import func, select

@router.get("/status")
async def get_system_status(db: AsyncSession = Depends(get_db)):
    """
    Returns system orchestration status, database health, and collected row counts.
    Used by frontend dashboard to display active monitoring state.
    """
    try:
        # 1. Row counts
        video_count_stmt = select(func.count(Video.video_id))
        video_res = await db.execute(video_count_stmt)
        total_videos = video_res.scalar()

        channel_count_stmt = select(func.count(Channel.channel_id))
        channel_res = await db.execute(channel_count_stmt)
        total_channels = channel_res.scalar()

        # 2. Latest rank update time
        latest_rank_stmt = select(VideoRank.updated_at).order_by(VideoRank.updated_at.desc()).limit(1)
        latest_rank_res = await db.execute(latest_rank_stmt)
        latest_rank_time = latest_rank_res.scalar()

        return {
            "status": "online",
            "database_health": "good",
            "total_videos": total_videos,
            "total_channels": total_channels,
            "latest_rank_update": latest_rank_time.isoformat() if latest_rank_time else None,
            "scheduler_interval_minutes": 5
        }
    except Exception as e:
        logger.error(f"Failed to fetch system status: {e}")
        return {
            "status": "degraded",
            "database_health": "offline/error",
            "error_detail": str(e),
            "total_videos": 0,
            "total_channels": 0,
            "latest_rank_update": None,
            "scheduler_interval_minutes": 5
        }


import json as _json
import os as _os

_TUNNEL_URL_FILE = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "tunnel_url.json")

@router.get("/tunnel-url")
async def get_tunnel_url():
    """
    현재 활성 Cloudflare 터널 URL을 반환합니다.
    프론트엔드가 localhost:8000을 통해 이 엔드포인트를 호출하여
    터널 URL이 바뀌었을 때 자동으로 최신 URL을 획득할 수 있습니다.
    """
    try:
        if _os.path.exists(_TUNNEL_URL_FILE):
            with open(_TUNNEL_URL_FILE, "r", encoding="utf-8") as f:
                data = _json.load(f)
            return data
        else:
            return {"tunnel_url": None, "api_url": None, "updated_at": None}
    except Exception as e:
        return {"tunnel_url": None, "api_url": None, "error": str(e)}
