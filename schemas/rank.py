from datetime import datetime, date
from pydantic import BaseModel, ConfigDict
from schemas.video import VideoResponse
from schemas.channel import ChannelResponse

class VideoRankResponse(BaseModel):
    id: int
    video_id: str
    rank: int
    virality_score: float
    is_shorts: bool
    period: str
    country_code: str
    rank_date: date
    updated_at: datetime
    video: VideoResponse

    model_config = ConfigDict(from_attributes=True)

class ChannelRankResponse(BaseModel):
    id: int
    channel_id: str
    rank: int
    growth_rate: float
    subscriber_count: int
    period: str
    country_code: str
    rank_date: date
    updated_at: datetime
    channel: ChannelResponse

    model_config = ConfigDict(from_attributes=True)

class RankingHistoryResponse(BaseModel):
    id: int
    video_id: str
    rank: int
    virality_score: float
    views: int
    likes: int
    comments: int
    country_code: str
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)
