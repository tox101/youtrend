from typing import Sequence, List
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository import RankRepository
from models.rank import VideoRank, RankingHistory

class RankingService:
    """
    Business logic coordinator for Rankings.
    Manages daily/weekly/monthly charts for Longform and Shorts.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.rank_repo = RankRepository(db)

    async def get_video_rankings(
        self, country_code: str, is_shorts: bool, period: str = "daily", limit: int = 100
    ) -> Sequence[VideoRank]:
        """
        Fetch top videos based on country, content type, and period.
        Supports Top 50 / Top 100 limit scales.
        """
        # Validate period
        clean_period = period.lower()
        if clean_period not in ["daily", "weekly", "monthly"]:
            clean_period = "daily"
        
        # Max limit check to avoid DB overhead
        clean_limit = min(max(limit, 1), 100)

        return await self.rank_repo.get_top_videos(
            country_code=country_code,
            is_shorts=is_shorts,
            period=clean_period,
            limit=clean_limit
        )

    async def get_video_rank_history(self, video_id: str, limit: int = 50) -> Sequence[RankingHistory]:
        """
        Fetch the ranking movements for visualization on timeline charts.
        """
        return await self.rank_repo.get_ranking_history(video_id, limit)

