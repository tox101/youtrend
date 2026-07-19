from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from services.video_service import VideoService

router = APIRouter(prefix="/compare", tags=["Comparison"])

@router.get("", response_model=List[Dict[str, Any]])
async def compare_video_regions(
    video_id: str = Query(..., description="The YouTube Video ID to compare"),
    db: AsyncSession = Depends(get_db)
):
    """
    Compare ranking positions and virality scores of a single video across all 8 regions (Country Diff).
    """
    service = VideoService(db)
    results = await service.get_country_diff(video_id=video_id)
    return results
