from typing import Sequence, Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
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

    async def get_videos_filtered(
        self,
        q: Optional[str] = None,
        target_age: Optional[str] = None,
        target_gender: Optional[str] = None,
        country_code: Optional[str] = None,
        category: Optional[str] = None,
        duration: Optional[str] = None,
        publish_date: Optional[str] = None,
        features: Optional[str] = None,
        sort_by: Optional[str] = "relevance",
        skip: int = 0,
        limit: int = 20
    ) -> List[Any]:
        import re
        import hashlib

        def parse_duration_to_seconds(d_str: Optional[str]) -> int:
            if not d_str:
                return 0
            pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
            match = pattern.match(d_str)
            if not match:
                return 0
            hours = int(match.group(1)) if match.group(1) else 0
            minutes = int(match.group(2)) if match.group(2) else 0
            seconds = int(match.group(3)) if match.group(3) else 0
            return hours * 3600 + minutes * 60 + seconds

        if category == "channel":
            # Search Channel table
            from models.channel import Channel
            ch_query = select(Channel)
            if q:
                ch_query = ch_query.where(Channel.title.contains(q) | Channel.description.contains(q))
            if country_code:
                ch_query = ch_query.where(Channel.country_code == country_code)
            
            if sort_by == "popularity":
                ch_query = ch_query.order_by(Channel.subscriber_count.desc())
            else:
                ch_query = ch_query.order_by(Channel.title.asc())
                
            ch_query = ch_query.offset(skip).limit(limit)
            ch_result = await self.db.execute(ch_query)
            channels = ch_result.scalars().all()

            mock_videos = []
            for ch in channels:
                # Wrap Channel details inside transient Video Response object
                mv = Video(
                    video_id=ch.channel_id,
                    title=ch.title,
                    description=ch.description,
                    country_code=ch.country_code,
                    publish_time=ch.published_at or datetime.now(timezone.utc),
                    views=ch.view_count or 0,
                    subscriber=ch.subscriber_count or 0,
                    thumbnail=ch.thumbnail_url,
                    isShort=False,
                    likes=0,
                    comments=0,
                    last_updated=datetime.now(timezone.utc),
                    channel=ch
                )
                mv.is_channel = True
                mock_videos.append(mv)
            return mock_videos

        # Standard Video search
        query = select(Video).options(joinedload(Video.channel))
        conditions = []

        if country_code:
            conditions.append(Video.country_code == country_code)

        if q:
            conditions.append(Video.title.contains(q) | Video.description.contains(q))

        if target_age and target_age != "all":
            if target_age == "50대이상":
                conditions.append(Video.target_age.in_(["50대", "60대이상"]))
            else:
                conditions.append(Video.target_age == target_age)

        if target_gender and target_gender != "전체":
            if target_gender in ["남성", "여성"]:
                conditions.append(Video.target_gender.in_([target_gender, "공통"]))
            else:
                conditions.append(Video.target_gender == target_gender)

        if category == "video":
            conditions.append(Video.isShort == False)
        elif category == "shorts":
            conditions.append(Video.isShort == True)

        if publish_date:
            now = datetime.now(timezone.utc)
            if publish_date == "today":
                conditions.append(Video.publish_time >= now - timedelta(days=1))
            elif publish_date == "this_week":
                conditions.append(Video.publish_time >= now - timedelta(days=7))
            elif publish_date == "this_month":
                conditions.append(Video.publish_time >= now - timedelta(days=30))

        if conditions:
            query = query.where(and_(*conditions))

        if sort_by == "popularity":
            query = query.order_by(Video.views.desc())
        else:
            # Default or relevance: sort by publish_time descending (newest first)
            query = query.order_by(Video.publish_time.desc())

        result = await self.db.execute(query)
        videos = list(result.scalars().unique().all())

        # Perform Python side filtering for duration and features if specified
        filtered_videos = []
        for v in videos:
            v.is_channel = False
            
            # Filter duration
            if duration:
                secs = parse_duration_to_seconds(v.duration)
                if duration == "under_3" and secs >= 180:
                    continue
                elif duration == "3_to_20" and (secs < 180 or secs > 1200):
                    continue
                elif duration == "over_20" and secs <= 1200:
                    continue

            # Filter features
            if features:
                # Features simulation based on hash stability
                h = int(hashlib.md5(v.video_id.encode('utf-8')).hexdigest(), 16)
                is_live = (h % 13 == 0)
                is_4k = (h % 7 == 0)
                is_hd = (h % 3 == 0)
                
                if features == "live" and not is_live:
                    continue
                elif features == "4k" and not is_4k:
                    continue
                elif features == "hd" and not is_hd:
                    continue

            filtered_videos.append(v)

        # Apply pagination after Python-side filtering
        paginated_videos = filtered_videos[skip : skip + limit]
        return paginated_videos

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

    async def get_trend_radar(self, country_code: str, hours: int = 24, limit: int = 100) -> List[Video]:
        """
        Trend Radar: Trending videos filtered by publish_time within the last N hours,
        ordered by views descending. Falls back to 7 days if no results found in the window.
        """
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        conditions = [Video.country_code == country_code, Video.publish_time >= since]

        query = (
            select(Video)
            .where(and_(*conditions))
            .options(joinedload(Video.channel))
            .order_by(Video.views.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        videos = list(result.scalars().all())

        # Fallback: if no results within the window, widen to 7 days
        if not videos:
            fallback_since = datetime.now(timezone.utc) - timedelta(days=7)
            fallback_query = (
                select(Video)
                .where(Video.country_code == country_code, Video.publish_time >= fallback_since)
                .options(joinedload(Video.channel))
                .order_by(Video.views.desc())
                .limit(limit)
            )
            fallback_result = await self.db.execute(fallback_query)
            videos = list(fallback_result.scalars().all())

        return videos

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
