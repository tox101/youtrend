import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from models.country import Country
from models.channel import Channel
from models.video import Video
from ranking.engine import RankingEngine
from database.repository import CountryRepository, ChannelRepository, VideoRepository

@pytest.mark.asyncio
async def test_virality_score_and_decay(test_db_session: AsyncSession):
    """
    Test that the Virality score computation performs correctly
    and decay decreases scores on older videos.
    """
    engine = RankingEngine(test_db_session)

    # Setup baseline entities
    country = Country(code="KR", name="Korea", is_active=True)
    test_db_session.add(country)
    
    channel = Channel(
        channel_id="ch_k",
        title="K-pop Channel",
        country_code="KR",
        subscriber_count=100000,
        view_count=500000,
        video_count=20
    )
    test_db_session.add(channel)
    await test_db_session.commit()

    # Case 1: Fresh video (just uploaded, high views)
    fresh_video = Video(
        video_id="fresh_01",
        title="Fresh Viral Hit",
        channel_id="ch_k",
        country_code="KR",
        publish_time=datetime.now(timezone.utc) - timedelta(hours=1), # 1 hr ago
        views=20000,
        likes=3000,
        comments=400,
        subscriber=100000,
        isShort=False
    )

    # Case 2: Old video (uploaded 10 days ago, same views/engagement)
    old_video = Video(
        video_id="old_01",
        title="Old Viral Hit",
        channel_id="ch_k",
        country_code="KR",
        publish_time=datetime.now(timezone.utc) - timedelta(days=10), # 240 hrs ago
        views=20000,
        likes=3000,
        comments=400,
        subscriber=100000,
        isShort=False
    )

    # Calculate raw scores
    fresh_score = engine.calculate_virality_score(fresh_video)
    old_score = engine.calculate_virality_score(old_video)

    # Asserts
    assert fresh_score > 0
    assert old_score > 0
    # Time decay must strictly degrade the older video score
    assert fresh_score > old_score
    logger_msg = f"Fresh Score: {fresh_score:.2f} vs Old Score: {old_score:.2f}"
    print(logger_msg)
