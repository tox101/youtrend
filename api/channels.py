from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from services.channel_service import ChannelService
from schemas.channel import ChannelResponse

router = APIRouter(prefix="/channels", tags=["Channels"])

@router.get("", response_model=List[ChannelResponse])
async def read_channels(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a list of indexed channels.
    """
    service = ChannelService(db)
    channels = await service.get_channels(skip=skip, limit=limit)
    return channels

@router.get("/creator-radar", response_model=List[ChannelResponse])
async def read_creator_radar(
    country_code: str = Query("KR", description="Country code (e.g. KR, US, GLOBAL)"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Identify micro channels experiencing a surge in views relative to subscriber sizes.
    """
    service = ChannelService(db)
    radar = await service.get_creator_radar(country_code=country_code.upper(), limit=limit)
    return radar

@router.get("/{channel_id}", response_model=ChannelResponse)
async def read_channel(
    channel_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get details for a specific channel.
    """
    service = ChannelService(db)
    channel = await service.get_channel_by_id(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel
