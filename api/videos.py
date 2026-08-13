from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from services.video_service import VideoService
from schemas.video import VideoResponse

router = APIRouter(prefix="/videos", tags=["Videos"])

@router.get("", response_model=List[VideoResponse])
async def read_videos(
    q: Optional[str] = Query(None, description="Search query"),
    target_age: Optional[str] = Query(None, description="Target age filter ('40대', '50대이상')"),
    target_gender: Optional[str] = Query(None, description="Target gender filter ('남성', '여성', '공통')"),
    country_code: Optional[str] = Query(None, description="Country code filter (e.g. 'KR', 'US', 'JP')"),
    category: Optional[str] = Query(None, description="Category filter ('video', 'shorts', 'channel')"),
    duration: Optional[str] = Query(None, description="Duration filter ('under_3', '3_to_20', 'over_20')"),
    publish_date: Optional[str] = Query(None, description="Upload date filter ('today', 'this_week', 'this_month')"),
    features: Optional[str] = Query(None, description="Features filter ('live', '4k', 'hd')"),
    sort_by: Optional[str] = Query("relevance", description="Sort by ('relevance', 'popularity')"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a list of all indexed videos with search query and pagination/filtering.
    """
    service = VideoService(db)
    videos = await service.get_videos_filtered(
        q=q,
        target_age=target_age,
        target_gender=target_gender,
        country_code=country_code.upper() if country_code else None,
        category=category,
        duration=duration,
        publish_date=publish_date,
        features=features,
        sort_by=sort_by,
        skip=skip,
        limit=limit
    )
    return videos

@router.get("/hidden-gems", response_model=List[VideoResponse])
async def read_hidden_gems(
    country_code: str = Query("KR", description="Country code (e.g. KR, US, GLOBAL)"),
    is_shorts: Optional[bool] = Query(None, description="Filter by Shorts (True) or Longform (False)"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Find 'Hidden Gems': high virality rate, low total views, high comment & like ratio.
    """
    service = VideoService(db)
    gems = await service.get_hidden_gems(country_code=country_code.upper(), is_shorts=is_shorts, limit=limit)
    return gems

@router.get("/{video_id}", response_model=VideoResponse)
async def read_video(
    video_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific video.
    """
    service = VideoService(db)
    video = await service.get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video
