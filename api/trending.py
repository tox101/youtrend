from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from services.video_service import VideoService
from schemas.video import VideoResponse

router = APIRouter(prefix="/trending", tags=["Trending (Radar)"])

@router.get("", response_model=List[VideoResponse])
async def read_trending_radar(
    country_code: str = Query("KR"),
    hours: int = Query(24, description="Trend window scale (e.g., 1, 3, 6, 12, 24 hours)", ge=1, le=168),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Trend Radar: Return top dynamic growth videos published within the last N hours.
    Falls back to 7-day window when no results exist in the given time range.
    """
    service = VideoService(db)
    trending_videos = await service.get_trend_radar(
        country_code=country_code.upper(),
        hours=hours,
        limit=limit
    )
    return trending_videos

