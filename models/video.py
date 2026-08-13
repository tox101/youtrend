from datetime import datetime
from typing import Optional, List
from sqlalchemy import ForeignKey, DateTime, func, BigInteger, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connection import Base

class Video(Base):
    __tablename__ = "videos"

    video_id: Mapped[str] = mapped_column(primary_key=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(nullable=True)
    channel_id: Mapped[str] = mapped_column(ForeignKey("channels.channel_id", ondelete="CASCADE"), nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(ForeignKey("countries.code"), nullable=False, index=True)
    language: Mapped[Optional[str]] = mapped_column(nullable=True)
    publish_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    duration: Mapped[Optional[str]] = mapped_column(nullable=True) # ISO 8601 duration
    
    # Statistical Fields at Crawl Time
    views: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    likes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    comments: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    subscriber: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False) # Channel sub count at capture time
    
    thumbnail: Mapped[Optional[str]] = mapped_column(nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True) # list of tags
    category: Mapped[Optional[str]] = mapped_column(nullable=True)
    isShort: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    target_age: Mapped[Optional[str]] = mapped_column(nullable=True, index=True, default="all")
    target_gender: Mapped[Optional[str]] = mapped_column(nullable=True, index=True, default="공통")
    
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    # Relationships
    channel: Mapped["Channel"] = relationship(back_populates="videos")
    country: Mapped["Country"] = relationship(back_populates=None)
    comments_list: Mapped[list["Comment"]] = relationship(back_populates="video", cascade="all, delete-orphan")
    ai_analysis: Mapped[Optional["AIAnalysis"]] = relationship(back_populates="video", uselist=False, cascade="all, delete-orphan")
    thumbnail_analysis: Mapped[Optional["ThumbnailAnalysis"]] = relationship(back_populates="video", uselist=False, cascade="all, delete-orphan")
    title_analysis: Mapped[Optional["TitleAnalysis"]] = relationship(back_populates="video", uselist=False, cascade="all, delete-orphan")
    trend_prediction: Mapped[Optional["TrendPrediction"]] = relationship(back_populates="video", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Video(id={self.video_id}, title={self.title[:20]}...)>"
