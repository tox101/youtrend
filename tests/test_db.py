import pytest
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.country import Country
from models.channel import Channel
from models.video import Video
from database.repository import CountryRepository, ChannelRepository, VideoRepository

@pytest.mark.asyncio
async def test_country_crud(test_db_session: AsyncSession):
    """Verifies that Country model CRUD works correctly."""
    repo = CountryRepository(test_db_session)
    
    # 1. Create
    country = Country(code="KR", name="South Korea", is_active=True)
    await repo.create(country)
    await test_db_session.commit()
    
    # 2. Read
    fetched = await repo.get_by_id("KR")
    assert fetched is not None
    assert fetched.name == "South Korea"
    
    # 3. Update
    await repo.update("KR", {"name": "Rep. of Korea"})
    await test_db_session.commit()
    
    updated = await repo.get_by_id("KR")
    assert updated.name == "Rep. of Korea"
    
    # 4. Delete
    deleted_ok = await repo.delete("KR")
    await test_db_session.commit()
    assert deleted_ok is True
    
    null_country = await repo.get_by_id("KR")
    assert null_country is None


@pytest.mark.asyncio
async def test_channel_and_video_relationships(test_db_session: AsyncSession):
    """Verifies relational integrity between Country, Channel, and Video."""
    country_repo = CountryRepository(test_db_session)
    channel_repo = ChannelRepository(test_db_session)
    video_repo = VideoRepository(test_db_session)

    # Setup Country
    country = Country(code="US", name="United States", is_active=True)
    await country_repo.create(country)

    # Setup Channel
    channel = Channel(
        channel_id="UC_123",
        title="Test Channel",
        country_code="US",
        subscriber_count=10000,
        view_count=50000,
        video_count=12
    )
    await channel_repo.create(channel)
    await test_db_session.commit()

    # Setup Video
    video = Video(
        video_id="vid_999",
        title="Epic Video",
        channel_id="UC_123",
        country_code="US",
        publish_time=datetime.now(timezone.utc),
        views=1500,
        likes=200,
        comments=45,
        subscriber=10000,
        isShort=False
    )
    await video_repo.create(video)
    await test_db_session.commit()

    # Verify relationships & Eager Loading to protect against N+1 queries
    fetched_video = await video_repo.get_video_with_details("vid_999")
    assert fetched_video is not None
    assert fetched_video.channel.title == "Test Channel"
    assert fetched_video.channel.subscriber_count == 10000
    assert fetched_video.country.name == "United States"
