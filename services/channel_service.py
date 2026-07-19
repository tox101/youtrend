from typing import Sequence, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.repository import ChannelRepository
from models.channel import Channel

class ChannelService:
    """
    Business logic coordinator for YouTube channels.
    Focuses on stats extraction and the 'Creator Radar' algorithm.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.channel_repo = ChannelRepository(db)

    async def get_channel_by_id(self, channel_id: str) -> Optional[Channel]:
        """Fetch details of a specific channel."""
        return await self.channel_repo.get_by_channel_id(channel_id)

    async def get_channels(self, skip: int = 0, limit: int = 100) -> Sequence[Channel]:
        """Fetch list of channels."""
        return await self.channel_repo.get_all(skip, limit)

    async def get_creator_radar(self, country_code: str, limit: int = 50) -> List[Channel]:
        """
        Creator Radar: Detects rising channels with relatively low subscriber counts
        but high audience interest and dynamic interactions.
        Criteria: Subscribers < 100,000; Minimum 1 video.
        Sorted by highest average views per video (efficiency/impact ratio).
        """
        query = (
            select(Channel)
            .where(
                Channel.country_code == country_code,
                Channel.subscriber_count.between(500, 100000),
                Channel.video_count > 0
            )
            .order_by((Channel.view_count / func.nullif(Channel.video_count, 0)).desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
