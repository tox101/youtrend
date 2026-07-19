from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from services.ai_service import AIService
from schemas.ai import AIAnalysisResponse, AIAnalysisRequest

router = APIRouter(prefix="/ai", tags=["AI Intelligence"])

@router.get("/{video_id}", response_model=AIAnalysisResponse)
async def get_video_ai_analysis(
    video_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get cached AI analysis report for a specific video.
    Returns 404 if no analysis exists yet.
    """
    service = AIService(db)
    analysis = await service.get_cached_analysis(video_id=video_id)
    if not analysis:
        raise HTTPException(
            status_code=404, 
            detail="AI analysis not found for this video. Trigger a new analysis via POST."
        )
    return analysis

@router.post("", response_model=AIAnalysisResponse)
async def trigger_video_ai_analysis(
    payload: AIAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger on-demand AI analysis for a video.
    Stores results in the cache database to prevent duplicate costs.
    """
    service = AIService(db)
    analysis = await service.generate_analysis(video_id=payload.video_id)
    return analysis
