from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class AIAnalysisResponse(BaseModel):
    video_id: str
    why_popular: str
    key_success_factors: str
    target_audience: str
    similar_contents: str
    prediction_24h: str
    improvement_ideas: str
    analyzed_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ThumbnailAnalysisResponse(BaseModel):
    video_id: str
    analysis_result: str
    dominant_colors: Optional[List[str]] = None
    object_tags: Optional[List[str]] = None
    aesthetic_score: float
    analyzed_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TitleAnalysisResponse(BaseModel):
    video_id: str
    analysis_result: str
    clickbait_score: float
    sentiment: str
    keywords: Optional[List[str]] = None
    analyzed_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TrendPredictionResponse(BaseModel):
    video_id: str
    trend_score: float
    predicted_views_24h: int
    confidence_score: float
    predicted_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Schema for requesting AI analysis
class AIAnalysisRequest(BaseModel):
    video_id: str
