from datetime import datetime, date
from sqlalchemy import ForeignKey, DateTime, Date, Float, Integer, BigInteger, Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connection import Base

class VideoRank(Base):
    __tablename__ = "video_rank"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.video_id", ondelete="CASCADE"), nullable=False, index=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    virality_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_shorts: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False, index=True) # 'daily', 'weekly', 'monthly'
    country_code: Mapped[str] = mapped_column(ForeignKey("countries.code"), nullable=False, index=True)
    rank_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    video: Mapped["Video"] = relationship()

    __table_args__ = (
        UniqueConstraint('video_id', 'period', 'country_code', 'rank_date', name='uq_video_rank_unique'),
        {"sqlite_autoincrement": True}
    )

    def __repr__(self) -> str:
        return f"<VideoRank(rank={self.rank}, video={self.video_id}, score={self.virality_score})>"


class ChannelRank(Base):
    __tablename__ = "channel_rank"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[str] = mapped_column(ForeignKey("channels.channel_id", ondelete="CASCADE"), nullable=False, index=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    growth_rate: Mapped[float] = mapped_column(Float, nullable=False)
    subscriber_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False, index=True) # 'daily', 'weekly', 'monthly'
    country_code: Mapped[str] = mapped_column(ForeignKey("countries.code"), nullable=False, index=True)
    rank_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    channel: Mapped["Channel"] = relationship()

    __table_args__ = (
        UniqueConstraint('channel_id', 'period', 'country_code', 'rank_date', name='uq_channel_rank_unique'),
        {"sqlite_autoincrement": True}
    )

    def __repr__(self) -> str:
        return f"<ChannelRank(rank={self.rank}, channel={self.channel_id}, growth={self.growth_rate})>"


class RankingHistory(Base):
    __tablename__ = "ranking_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.video_id", ondelete="CASCADE"), nullable=False, index=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    virality_score: Mapped[float] = mapped_column(Float, nullable=False)
    views: Mapped[int] = mapped_column(BigInteger, nullable=False)
    likes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    comments: Mapped[int] = mapped_column(BigInteger, nullable=False)
    country_code: Mapped[str] = mapped_column(ForeignKey("countries.code"), nullable=False, index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    # Relationship
    video: Mapped["Video"] = relationship()

    __table_args__ = (
        {"sqlite_autoincrement": True}
    )

    def __repr__(self) -> str:
        return f"<RankingHistory(video={self.video_id}, rank={self.rank}, time={self.recorded_at})>"
