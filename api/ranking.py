from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from services.ranking_service import RankingService
from schemas.rank import VideoRankResponse, RankingHistoryResponse

router = APIRouter(tags=["Rankings"])

@router.get("/ranking", response_model=List[VideoRankResponse])
async def read_ranking(
    country_code: str = Query("KR"),
    is_shorts: bool = Query(False),
    period: str = Query("daily", description="'daily', 'weekly', or 'monthly'"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    General endpoint to fetch YouTube video ranks.
    """
    service = RankingService(db)
    ranks = await service.get_video_rankings(
        country_code=country_code.upper(),
        is_shorts=is_shorts,
        period=period,
        limit=limit
    )
    return ranks

@router.get("/shorts", response_model=List[VideoRankResponse])
async def read_shorts_ranking(
    country_code: str = Query("KR"),
    period: str = Query("daily"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get top Shorts rankings (Top 50 / Top 100).
    """
    service = RankingService(db)
    return await service.get_video_rankings(
        country_code=country_code.upper(),
        is_shorts=True,
        period=period,
        limit=limit
    )

@router.get("/longform", response_model=List[VideoRankResponse])
async def read_longform_ranking(
    country_code: str = Query("KR"),
    period: str = Query("daily"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get top Longform rankings (Top 50 / Top 100).
    """
    service = RankingService(db)
    return await service.get_video_rankings(
        country_code=country_code.upper(),
        is_shorts=False,
        period=period,
        limit=limit
    )

@router.get("/ranking/history/{video_id}", response_model=List[RankingHistoryResponse])
async def read_ranking_history(
    video_id: str,
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical rank movements of a video (for timelines and charts).
    """
    service = RankingService(db)
    history = await service.get_video_rank_history(video_id=video_id, limit=limit)
    return history
