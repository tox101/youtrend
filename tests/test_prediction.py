import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from models.video import Video
from ranking.prediction_model import VideoViewsPredictor

@pytest.mark.asyncio
async def test_prediction_math_fallback(test_db_session: AsyncSession):
    """
    Validates that the VideoViewsPredictor correctly computes
    a mathematical projection when the dataset is too small for XGBoost.
    """
    predictor = VideoViewsPredictor(test_db_session)

    # Create a fresh video (2 hours old, 10K views)
    fresh_video = Video(
        video_id="pred_01",
        title="Prediction Test Video",
        channel_id="ch_test",
        country_code="KR",
        publish_time=datetime.now(timezone.utc) - timedelta(hours=2),
        views=10000,
        likes=800,
        comments=120,
        subscriber=50000,
        isShort=False
    )

    predicted_views, confidence = await predictor.predict_24h_views(fresh_video)

    # Prediction must exceed current views (growth projection)
    assert predicted_views >= fresh_video.views
    # Confidence must be between 0 and 1
    assert 0.0 < confidence <= 1.0

    print(f"Math Fallback Prediction: {predicted_views:,} views (Confidence: {confidence:.0%})")


@pytest.mark.asyncio
async def test_prediction_shorts_vs_longform(test_db_session: AsyncSession):
    """
    Validates that Shorts videos decay faster than Longform
    in the math projection fallback.
    """
    predictor = VideoViewsPredictor(test_db_session)

    base_params = dict(
        channel_id="ch_test",
        country_code="KR",
        publish_time=datetime.now(timezone.utc) - timedelta(hours=3),
        views=5000,
        likes=400,
        comments=60,
        subscriber=20000,
    )

    longform_video = Video(video_id="pred_lf", title="Longform Test", isShort=False, **base_params)
    shorts_video = Video(video_id="pred_sh", title="Shorts Test", isShort=True, **base_params)

    lf_predicted, _ = await predictor.predict_24h_views(longform_video)
    sh_predicted, _ = await predictor.predict_24h_views(shorts_video)

    # Longform should project higher because alpha is higher (slower decay)
    assert lf_predicted >= sh_predicted

    print(f"Longform: {lf_predicted:,} vs Shorts: {sh_predicted:,}")
