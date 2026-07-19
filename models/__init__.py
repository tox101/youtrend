from database.connection import Base
from models.country import Country
from models.channel import Channel
from models.video import Video
from models.rank import VideoRank, ChannelRank, RankingHistory
from models.analysis import AIAnalysis, ThumbnailAnalysis, TitleAnalysis, TrendPrediction
from models.interaction import Comment, Alert, User, Favorite

# Export all models for easier imports and Alembic autogenerate tracking
__all__ = [
    "Base",
    "Country",
    "Channel",
    "Video",
    "VideoRank",
    "ChannelRank",
    "RankingHistory",
    "AIAnalysis",
    "ThumbnailAnalysis",
    "TitleAnalysis",
    "TrendPrediction",
    "Comment",
    "Alert",
    "User",
    "Favorite",
]
