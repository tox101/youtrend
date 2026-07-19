from typing import Generic, TypeVar, Type, List, Optional, Any, Sequence
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from database.connection import Base
from models.country import Country
from models.channel import Channel
from models.video import Video
from models.rank import VideoRank, ChannelRank, RankingHistory
from models.analysis import AIAnalysis, ThumbnailAnalysis, TitleAnalysis, TrendPrediction
from models.interaction import Comment, Alert, User, Favorite

T = TypeVar("T", bound=Base)

class GenericRepository(Generic[T]):
    """
    Base Repository implementing CRUD operations using SQLAlchemy 2.0 Async Session.
    Ensures SOLID principles by decoupling data storage access from service logic.
    """
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id_val: Any) -> Optional[T]:
        """Fetch a single record by primary key."""
        return await self.session.get(self.model, id_val)

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[T]:
        """Fetch all records with optional offset and limit."""
        query = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create(self, entity: T) -> T:
        """Persist a new entity instance to the database."""
        self.session.add(entity)
        return entity

    async def update(self, id_val: Any, update_data: dict[str, Any]) -> Optional[T]:
        """Update an existing record with a dictionary of values."""
        query = (
            update(self.model)
            .where(getattr(self.model, self._primary_key_name()) == id_val)
            .values(**update_data)
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(query)
        return await self.get_by_id(id_val)

    async def delete(self, id_val: Any) -> bool:
        """Delete a record by primary key."""
        query = delete(self.model).where(getattr(self.model, self._primary_key_name()) == id_val)
        result = await self.session.execute(query)
        return result.rowcount > 0

    def _primary_key_name(self) -> str:
        """Helper to get primary key name from model mapper."""
        return self.model.__mapper__.primary_key[0].name


class CountryRepository(GenericRepository[Country]):
    def __init__(self, session: AsyncSession):
        super().__init__(Country, session)

    async def get_active_countries(self) -> Sequence[Country]:
        query = select(Country).where(Country.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()


class ChannelRepository(GenericRepository[Channel]):
    def __init__(self, session: AsyncSession):
        super().__init__(Channel, session)

    async def get_by_channel_id(self, channel_id: str) -> Optional[Channel]:
        # Avoid N+1 issues when reading related country
        query = select(Channel).where(Channel.channel_id == channel_id).options(joinedload(Channel.country))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def upsert_channel(self, channel: Channel) -> Channel:
        """Upsert a channel record using session.merge."""
        merged = await self.session.merge(channel)
        return merged


class VideoRepository(GenericRepository[Video]):
    def __init__(self, session: AsyncSession):
        super().__init__(Video, session)

    async def get_video_with_details(self, video_id: str) -> Optional[Video]:
        """
        Fetch video with all analysis parameters eagerly loaded to avoid N+1 queries in APIs.
        """
        query = (
            select(Video)
            .where(Video.video_id == video_id)
            .options(
                joinedload(Video.channel),
                selectinload(Video.comments_list),
                selectinload(Video.ai_analysis),
                selectinload(Video.thumbnail_analysis),
                selectinload(Video.title_analysis),
                selectinload(Video.trend_prediction)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_videos_by_country_and_type(
        self, country_code: str, is_shorts: bool, limit: int = 100
    ) -> Sequence[Video]:
        """Fetch videos by country and content type (Shorts/Longform)"""
        query = (
            select(Video)
            .where(Video.country_code == country_code, Video.isShort == is_shorts)
            .order_by(Video.views.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def upsert_video(self, video: Video) -> Video:
        """Upsert a video record using session.merge."""
        merged = await self.session.merge(video)
        return merged




class RankRepository:
    """Specialized Repository to query video and channel rankings"""
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_top_videos(
        self, country_code: str, is_shorts: bool, period: str, limit: int = 100
    ) -> Sequence[VideoRank]:
        """Fetch top ranked videos for dashboard rank views."""
        # Query the latest rank date for the given criteria to avoid duplicate dates in the list
        subquery = (
            select(func.max(VideoRank.rank_date))
            .where(
                VideoRank.country_code == country_code,
                VideoRank.is_shorts == is_shorts,
                VideoRank.period == period
            )
        )
        latest_date_result = await self.session.execute(subquery)
        latest_date = latest_date_result.scalar()

        if not latest_date:
            return []

        query = (
            select(VideoRank)
            .where(
                VideoRank.country_code == country_code,
                VideoRank.is_shorts == is_shorts,
                VideoRank.period == period,
                VideoRank.rank_date == latest_date
            )
            .options(joinedload(VideoRank.video).joinedload(Video.channel))
            .order_by(VideoRank.rank.asc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().unique().all()

    async def bulk_save_video_ranks(self, ranks: List[VideoRank]) -> None:
        """Batch insert or update ranking information."""
        # Using session.add_all for lightweight saving
        self.session.add_all(ranks)

    async def get_ranking_history(self, video_id: str, limit: int = 50) -> Sequence[RankingHistory]:
        """Fetch historical rank movements for timeline charts."""
        query = (
            select(RankingHistory)
            .where(RankingHistory.video_id == video_id)
            .order_by(RankingHistory.recorded_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()


class AnalysisRepository:
    """Manages AI evaluations and caching mechanisms"""
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_ai_analysis(self, video_id: str) -> Optional[AIAnalysis]:
        query = select(AIAnalysis).where(AIAnalysis.video_id == video_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def save_ai_analysis(self, analysis: AIAnalysis) -> AIAnalysis:
        self.session.add(analysis)
        return analysis

    async def get_title_analysis(self, video_id: str) -> Optional[TitleAnalysis]:
        query = select(TitleAnalysis).where(TitleAnalysis.video_id == video_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def save_title_analysis(self, analysis: TitleAnalysis) -> TitleAnalysis:
        self.session.add(analysis)
        return analysis

    async def get_thumbnail_analysis(self, video_id: str) -> Optional[ThumbnailAnalysis]:
        query = select(ThumbnailAnalysis).where(ThumbnailAnalysis.video_id == video_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


    async def save_thumbnail_analysis(self, analysis: ThumbnailAnalysis) -> ThumbnailAnalysis:
        self.session.add(analysis)
        return analysis
