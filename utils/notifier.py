import os
import logging
import httpx
from typing import Optional

logger = logging.getLogger("utils.notifier")
logging.basicConfig(level=logging.INFO)

async def send_discord_alert(
    video_title: str,
    video_id: str,
    score: float,
    alert_type: str,
    thumbnail_url: Optional[str] = None,
    views: int = 0
) -> bool:
    """
    Sends a rich embed notification card to a configured Discord channel via Webhook.
    Triggers automatically when a video scores high virality (>=95) or is flagged as a Hidden Gem.
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    if not webhook_url:
        logger.info(f"Discord Alert [Skipped - Webhook URL not set in .env]: Video {video_id} score {score} ({alert_type})")
        return False

    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Theme color configuration: Magenta for Hot Virality, Emerald Green for Hidden Gems
    color_hex = 0xef4444 if score >= 95 else 0x10b981
    
    # Build discord embed format
    payload = {
        "username": "YouTube Intelligence Platform",
        "avatar_url": "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?q=80&w=128&auto=format&fit=crop",
        "embeds": [
            {
                "title": f"🚨 {alert_type.upper()} ALERT DETECTED!",
                "description": f"**[{video_title}]({video_url})**",
                "color": color_hex,
                "fields": [
                    {
                        "name": "Virality Score",
                        "value": f"🏆 **{score:.1f} / 100점**",
                        "inline": True
                    },
                    {
                        "name": "현재 조회수",
                        "value": f"👁 **{views:,}회**",
                        "inline": True
                    },
                    {
                        "name": "유튜브 링크",
                        "value": f"[바로가기]({video_url})",
                        "inline": True
                    }
                ],
                "image": {
                    "url": thumbnail_url or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                },
                "footer": {
                    "text": "YouTube Global Intelligence System • Realtime Monitor",
                    "icon_url": "https://img.icons8.com/color/48/youtube-play.png"
                }
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=payload)
            if response.status_code in [200, 204]:
                logger.info(f"Discord Webhook Alert sent successfully for video {video_id}.")
                return True
            else:
                logger.error(f"Discord Webhook returned status code: {response.status_code}. Response: {response.text}")
                return False
    except Exception as e:
        logger.error(f"Failed to post Discord alert: {e}", exc_info=True)
        return False
