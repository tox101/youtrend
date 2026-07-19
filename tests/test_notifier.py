import pytest
import httpx
from unittest.mock import AsyncMock, patch
from utils.notifier import send_discord_alert

@pytest.mark.asyncio
async def test_discord_alert_skips_when_no_url():
    """
    Verifies that Discord alerting gracefully skips
    when DISCORD_WEBHOOK_URL is not set in environment.
    """
    with patch.dict("os.environ", {"DISCORD_WEBHOOK_URL": ""}, clear=False):
        result = await send_discord_alert(
            video_title="Test Video",
            video_id="vid_test_123",
            score=97.5,
            alert_type="VIRALITY",
            views=500000
        )
        assert result is False  # Should skip without error


@pytest.mark.asyncio
async def test_discord_alert_sends_when_url_set():
    """
    Verifies that Discord alerting sends HTTP POST
    when a valid DISCORD_WEBHOOK_URL is configured.
    Uses mock to avoid actually hitting Discord API.
    """
    mock_response = AsyncMock()
    mock_response.status_code = 204
    mock_response.text = ""

    with patch.dict("os.environ", {"DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/test/mock"}, clear=False):
        with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
            result = await send_discord_alert(
                video_title="Viral Hit Video",
                video_id="vid_viral_456",
                score=98.2,
                alert_type="VIRALITY",
                views=1200000
            )
            assert result is True
            mock_post.assert_called_once()
