from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from schemas.channel import ChannelResponse

class VideoBase(BaseModel):
    video_id: str
    title: str
    description: Optional[str] = None
    country_code: str
    language: Optional[str] = None
    publish_time: datetime
    duration: Optional[str] = None
    thumbnail: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    isShort: bool
    target_age: Optional[str] = None
    target_gender: Optional[str] = None

class VideoCreate(VideoBase):
    channel_id: str
    views: int
    likes: int
    comments: int
    subscriber: int

class VideoResponse(VideoBase):
    views: int
    likes: int
    comments: int
    subscriber: int
    last_updated: datetime
    channel: Optional[ChannelResponse] = None
    is_channel: bool = False

    model_config = ConfigDict(from_attributes=True)
