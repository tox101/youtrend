from datetime import datetime
from typing import Optional, List
from sqlalchemy import ForeignKey, DateTime, Float, BigInteger, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connection import Base

class AIAnalysis(Base):
    __tablename__ = "ai_analysis"

    video_id: Mapped[str] = mapped_column(ForeignKey("videos.video_id", ondelete="CASCADE"), primary_key=True, index=True)
    why_popular: Mapped[str] = mapped_column(Text, nullable=False)
    key_success_factors: Mapped[str] = mapped_column(Text, nullable=False)
    target_audience: Mapped[str] = mapped_column(Text, nullable=False)
    similar_contents: Mapped[str] = mapped_column(Text, nullable=False)
    prediction_24h: Mapped[str] = mapped_column(Text, nullable=False)
    improvement_ideas: Mapped[str] = mapped_column(Text, nullable=False)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationship
    video: Mapped["Video"] = relationship(back_populates="ai_analysis")

    def __repr__(self) -> str:
        return f"<AIAnalysis(video_id={self.video_id}, analyzed_at={self.analyzed_at})>"


class ThumbnailAnalysis(Base):
    __tablename__ = "thumbnail_analysis"

    video_id: Mapped[str] = mapped_column(ForeignKey("videos.video_id", ondelete="CASCADE"), primary_key=True, index=True)
    analysis_result: Mapped[str] = mapped_column(Text, nullable=False)
    dominant_colors: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    object_tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    aesthetic_score: Mapped[float] = mapped_column(Float, default=0.0)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationship
    video: Mapped["Video"] = relationship(back_populates="thumbnail_analysis")

    def __repr__(self) -> str:
        return f"<ThumbnailAnalysis(video_id={self.video_id})>"


class TitleAnalysis(Base):
    __tablename__ = "title_analysis"

    video_id: Mapped[str] = mapped_column(ForeignKey("videos.video_id", ondelete="CASCADE"), primary_key=True, index=True)
    analysis_result: Mapped[str] = mapped_column(Text, nullable=False)
    clickbait_score: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment: Mapped[str] = mapped_column(String(50), default="neutral")
    keywords: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationship
    video: Mapped["Video"] = relationship(back_populates="title_analysis")

    def __repr__(self) -> str:
        return f"<TitleAnalysis(video_id={self.video_id})>"


class TrendPrediction(Base):
    __tablename__ = "trend_prediction"

    video_id: Mapped[str] = mapped_column(ForeignKey("videos.video_id", ondelete="CASCADE"), primary_key=True, index=True)
    trend_score: Mapped[float] = mapped_column(Float, default=0.0)
    predicted_views_24h: Mapped[int] = mapped_column(BigInteger, default=0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    predicted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationship
    video: Mapped["Video"] = relationship(back_populates="trend_prediction")

    def __repr__(self) -> str:
        return f"<TrendPrediction(video_id={self.video_id}, score={self.trend_score})>"
