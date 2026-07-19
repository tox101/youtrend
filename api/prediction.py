from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from database.connection import get_db
from database.repository import VideoRepository
from ranking.prediction_model import VideoViewsPredictor

router = APIRouter(prefix="/prediction", tags=["ML Prediction"])


class PredictionResponse(BaseModel):
    video_id: str
    current_views: int
    predicted_views_24h: int
    confidence: float
    model_type: str  # "xgboost" or "math_fallback"


@router.get("/{video_id}", response_model=PredictionResponse)
async def get_24h_prediction(
    video_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns a 24-hour cumulative views prediction for a given video.
    Uses XGBoost when enough data is available, otherwise falls back
    to a mathematical growth projection.
    """
    video_repo = VideoRepository(db)
    video = await video_repo.get_video_with_details(video_id)

    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found.")

    predictor = VideoViewsPredictor(db)
    predicted_views, confidence = await predictor.predict_24h_views(video)

    model_type = "xgboost" if confidence > 0.65 else "math_fallback"

    return PredictionResponse(
        video_id=video_id,
        current_views=video.views,
        predicted_views_24h=predicted_views,
        confidence=round(confidence, 2),
        model_type=model_type
    )
