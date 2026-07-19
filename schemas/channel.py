from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ChannelBase(BaseModel):
    channel_id: str
    title: str
    description: Optional[str] = None
    custom_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

class ChannelCreate(ChannelBase):
    country_code: str

class ChannelUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    custom_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    view_count: Optional[int] = None
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None

class ChannelResponse(ChannelBase):
    view_count: int
    subscriber_count: int
    video_count: int
    country_code: str
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)
