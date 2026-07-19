from datetime import datetime
from pydantic import BaseModel, ConfigDict
from schemas.video import VideoResponse

class AlertResponse(BaseModel):
    alert_id: int
    video_id: str
    type: str  # 'virality', 'hidden_gem', 'creator_radar'
    message: str
    is_read: bool
    created_at: datetime
    video: VideoResponse

    model_config = ConfigDict(from_attributes=True)
