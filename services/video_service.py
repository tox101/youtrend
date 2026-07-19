from typing import Sequence, Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload
from database.repository import VideoRepository, RankRepository
from models.video import Video
from models.rank import VideoRank
from models.country import Country

class VideoService:
    """
    Business logic coordinator for Video related operations.
    Combines repositories and handles data processing like Hidden Gem & Country Diff detection.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.video_repo = VideoRepository(db)
        self.rank_repo = RankRepository(db)

    async def get_video_by_id(self, video_id: str) -> Optional[Video]:
        """Fetch detail of a single video with preloaded associations."""
        return await self.video_repo.get_video_with_details(video_id)

    async def get_videos(self, skip: int = 0, limit: int = 100) -> Sequence[Video]:
        """Fetch general video list."""
        return await self.video_repo.get_all(skip, limit)

    async def get_hidden_gems(self, country_code: str, is_shorts: Optional[bool] = None, limit: int = 50) -> List[Video]:
        """
        Hidden Gems (Trending Overseas Adaptations): Rising overseas trends with high virality scores 
        that have NOT entered Korea or Japan yet. Perfect for quick domestic replication.
        """
        import re

        # Subquery: video_ids that have been ranked in KR or JP
        exclude_rank_subquery = (
            select(VideoRank.video_id)
            .where(VideoRank.country_code.in_(["KR", "JP"]))
        )

        conditions = [
            VideoRank.country_code.notin_(["KR", "JP"]),
            VideoRank.video_id.notin_(exclude_rank_subquery)
        ]

        if is_shorts is not None:
            conditions.append(VideoRank.is_shorts == is_shorts)

        # Query latest daily ranks with highest virality score (extremely trendy)
        query = (
            select(VideoRank)
            .where(and_(*conditions))
            .options(joinedload(VideoRank.video).joinedload(Video.channel))
            .order_by(VideoRank.virality_score.desc()) # Rising velocity & viral explosion rate
            .limit(limit * 5) # Compensate for text regex exclusions
        )
        result = await self.db.execute(query)
        ranks = list(result.scalars().all())

        # Extract videos, deduplicate and filter out Korean/Japanese language
        filtered_videos = []
        seen_ids = set()
        kr_jp_regex = re.compile(r"[\uac00-\ud7a3\u3040-\u309f\u30a0-\u30ff\u3131-\u318e]")

        for r in ranks:
            video = r.video
            if not video or video.video_id in seen_ids:
                continue
                
            text_to_check = (video.title or "") + " " + (video.description or "")
            if not kr_jp_regex.search(text_to_check):
                seen_ids.add(video.video_id)
                filtered_videos.append(video)
                if len(filtered_videos) >= limit:
                    break

        return filtered_videos

        # Filter out videos containing Korean or Japanese characters in title/description
        # to ensure it is purely unintroduced overseas content
        filtered_videos = []
        kr_jp_regex = re.compile(r"[\uac00-\ud7a3\u3040-\u309f\u30a0-\u30ff\u3131-\u318e]")
        
        for video in videos:
            text_to_check = (video.title or "") + " " + (video.description or "")
            if not kr_jp_regex.search(text_to_check):
                filtered_videos.append(video)
                if len(filtered_videos) >= limit:
                    break

        return filtered_videos

    async def get_trend_radar(self, country_code: str, limit: int = 100) -> List[Video]:
        """
        Trend Radar: Highly dynamic trending videos, ordered by views count descending.
        """
        query = (
            select(Video)
            .where(Video.country_code == country_code)
            .options(joinedload(Video.channel))
            .order_by(Video.views.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_country_diff(self, video_id: str) -> List[Dict[str, Any]]:
        """
        Country Diff: Tracks the rank of a single video across all 8 regions (KR, US, JP, IN, GB, CA, AU, GLOBAL).
        Returns a list of dicts with country details and corresponding ranks.
        """
        # Fetch active countries first
        country_query = select(Country).where(Country.is_active == True)
        country_result = await self.db.execute(country_query)
        countries = country_result.scalars().all()

        diff_results = []
        for country in countries:
            # Query the latest rank for this video in this country
            rank_query = (
                select(VideoRank)
                .where(
                    VideoRank.video_id == video_id,
                    VideoRank.country_code == country.code,
                    VideoRank.period == "daily" # Daily tracking default
                )
                .order_by(VideoRank.rank_date.desc())
                .limit(1)
            )
            rank_result = await self.db.execute(rank_query)
            latest_rank_record = rank_result.scalar_one_or_none()

            diff_results.append({
                "country_code": country.code,
                "country_name": country.name,
                "rank": latest_rank_record.rank if latest_rank_record else None,
                "virality_score": latest_rank_record.virality_score if latest_rank_record else None,
                "rank_date": latest_rank_record.rank_date if latest_rank_record else None
            })

        return diff_results
