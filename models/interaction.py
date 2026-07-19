from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, DateTime, Integer, Boolean, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connection import Base

class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    comment_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.video_id", ondelete="CASCADE"), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationship
    video: Mapped["Video"] = relationship(back_populates="comments_list")

    def __repr__(self) -> str:
        return f"<Comment(id={self.comment_id[:10]}..., author={self.author})>"


class Alert(Base):
    __tablename__ = "alerts"

    alert_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.video_id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'virality', 'hidden_gem', 'creator_radar'
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationship
    video: Mapped["Video"] = relationship()

    def __repr__(self) -> str:
        return f"<Alert(id={self.alert_id}, type={self.type})>"


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(email={self.email})>"


class Favorite(Base):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    video_id: Mapped[Optional[str]] = mapped_column(ForeignKey("videos.video_id", ondelete="CASCADE"), nullable=True, index=True)
    channel_id: Mapped[Optional[str]] = mapped_column(ForeignKey("channels.channel_id", ondelete="CASCADE"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="favorites")
    video: Mapped[Optional["Video"]] = relationship()
    channel: Mapped[Optional["Channel"]] = relationship()

    __table_args__ = (
        UniqueConstraint('user_id', 'video_id', name='uq_user_video_favorite'),
        UniqueConstraint('user_id', 'channel_id', name='uq_user_channel_favorite'),
    )

    def __repr__(self) -> str:
        return f"<Favorite(user={self.user_id}, video={self.video_id}, channel={self.channel_id})>"
