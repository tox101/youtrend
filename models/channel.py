from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, DateTime, func, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connection import Base

class Channel(Base):
    __tablename__ = "channels"

    channel_id: Mapped[str] = mapped_column(primary_key=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(nullable=True)
    custom_url: Mapped[Optional[str]] = mapped_column(nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(nullable=True)
    
    # Large numbers are stored in BigInteger to avoid overflow
    view_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    subscriber_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    video_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    
    country_code: Mapped[str] = mapped_column(ForeignKey("countries.code"), nullable=False, index=True)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    # Relationships
    country: Mapped["Country"] = relationship(back_populates=None)
    videos: Mapped[list["Video"]] = relationship(back_populates="channel", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Channel(id={self.channel_id}, title={self.title})>"
