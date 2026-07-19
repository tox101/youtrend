import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from database.connection import AsyncSessionLocal
from database.repository import CountryRepository, ChannelRepository, VideoRepository
from models.channel import Channel
from models.video import Video
from crawler.youtube_api import YouTubeAPIClient, YouTubeQuotaExceededException
from crawler.playwright_scraper import PlaywrightScraper

logger = logging.getLogger("crawler.collector")
logging.basicConfig(level=logging.INFO)

class DataCollector:
    """
    Orchestrates the crawling pipeline:
    Fetches trending content from YouTube API or falls back to Playwright Scraper.
    Saves parsed channel and video records into PostgreSQL database.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_client = YouTubeAPIClient(api_key=api_key)
        self.scraper = PlaywrightScraper(headless=True)

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Safely parses ISO 8601 timestamps returned by YouTube API (handles Z, milliseconds, etc.)."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return datetime.now(timezone.utc)

    def parse_iso8601_duration_to_seconds(self, duration_str: str) -> int:

        """Converts ISO 8601 duration (e.g., PT1M30S) into integer seconds."""
        pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
        match = pattern.match(duration_str)
        if not match:
            return 0
        
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = int(match.group(3)) if match.group(3) else 0
        
        return hours * 3600 + minutes * 60 + seconds

    def check_is_shorts(self, duration_str: Optional[str], title: str, tags: Optional[List[str]]) -> bool:
        """Determines if a video is a YouTube Short based on duration, tags, and title."""
        if duration_str:
            seconds = self.parse_iso8601_duration_to_seconds(duration_str)
            if seconds > 0 and seconds <= 60:
                return True
            if seconds > 60:
                return False
        
        # Fallback check on text metadata
        title_lower = title.lower()
        if "#shorts" in title_lower or "shorts" in title_lower:
            return True
        
        if tags:
            tag_string = "".join(tags).lower()
            if "shorts" in tag_string or "short" in tag_string:
                return True

        return False

    async def collect_for_country(self, country_code: str) -> None:
        """
        Collects trending videos (Longform and Shorts) for a given country.
        Gracefully switches to Playwright if API Quota is exceeded.
        """
        logger.info(f"=== Starting collection for Country: {country_code} ===")
        
        # 1. Collect Longform / Standard Trending
        try:
            logger.info("Fetching trending via YouTube API...")
            api_videos = self.api_client.get_trending_videos(country_code, max_results=100)
            await self._process_api_videos(country_code, api_videos)
        except YouTubeQuotaExceededException:
            logger.warning("YouTube API Quota exceeded. Falling back to Playwright Scraper for Longform.")
            scraped_videos = await self.scraper.scrape_trending(country_code, is_shorts=False, limit=50)
            await self._process_scraped_videos(country_code, scraped_videos, is_shorts=False)
        except Exception as e:
            logger.error(f"Failed to collect API videos for {country_code}: {e}", exc_info=True)
            # Try Playwright fallback anyways on unexpected API error
            try:
                scraped_videos = await self.scraper.scrape_trending(country_code, is_shorts=False, limit=50)
                await self._process_scraped_videos(country_code, scraped_videos, is_shorts=False)
            except Exception as pe:
                logger.error(f"Playwright fallback also failed for {country_code}: {pe}")

        # 2. Collect Shorts Trending
        try:
            # Try Playwright first for Shorts
            logger.info("Scraping Shorts via Playwright...")
            scraped_shorts = await self.scraper.scrape_trending(country_code, is_shorts=True, limit=50)
            if scraped_shorts:
                await self._process_scraped_videos(country_code, scraped_shorts, is_shorts=True)
            else:
                # Playwright failed or returned empty — fallback to YouTube API shorts extraction
                logger.info("Playwright returned empty. Fetching Shorts from YouTube API (short-duration filter)...")
                await self._collect_shorts_via_api(country_code)
        except Exception as e:
            logger.error(f"Failed to collect Shorts for {country_code}: {e}", exc_info=True)
            # Last resort: try API shorts
            try:
                await self._collect_shorts_via_api(country_code)
            except Exception:
                pass

    async def _collect_shorts_via_api(self, country_code: str) -> None:
        """Fetch trending short videos from YouTube Search API by querying multiple localized hashtags and filtering true Shorts (<=60s)."""
        try:
            region_code = country_code if country_code != "GLOBAL" else "US"
            # Search for recent shorts with wider time window (14 days)
            from datetime import timedelta
            fourteen_days_ago = (datetime.now(timezone.utc) - timedelta(days=14)).strftime("%Y-%m-%dT00:00:00Z")
            
            # ISO 639-1 language code mapping (country code -> language code)
            LANG_MAP = {
                "KR": "ko", "US": "en", "JP": "ja", "IN": "hi",
                "GB": "en", "CA": "en", "AU": "en", "GLOBAL": "en",
            }
            lang_code = LANG_MAP.get(country_code, "en")
            
            # Formulate localized list of hashtags to query sequentially for richer results
            if country_code == "KR":
                queries = ["#shorts", "#쇼츠", "#숏폼", "#short", "인기 숏츠"]
            elif country_code == "JP":
                queries = ["#shorts", "#ショート", "#ショート動画", "#tiktok", "人気ショート"]
            elif country_code == "IN":
                queries = ["#shorts", "#trending", "#viral", "#funny", "#reels"]
            else:
                queries = ["#shorts", "#trending", "#tiktok", "#funny", "#viral"]
            
            unique_video_ids = set()
            
            # Query each keyword with two ordering strategies for maximum coverage
            for query in queries:
                for order_type in ["viewCount", "date"]:
                    try:
                        request = self.api_client.youtube.search().list(
                            part="id",
                            type="video",
                            q=query,
                            videoDuration="short",  # YouTube API filter: under 4min
                            order=order_type,
                            regionCode=region_code,
                            relevanceLanguage=lang_code,
                            maxResults=25,
                            publishedAfter=fourteen_days_ago
                        )
                        response = request.execute()
                        for item in response.get("items", []):
                            vid = item["id"].get("videoId")
                            if vid:
                                unique_video_ids.add(vid)
                    except Exception as query_err:
                        logger.warning(f"Shorts sub-query '{query}' (order={order_type}) failed for {country_code}: {query_err}")
            
            if not unique_video_ids:
                logger.info(f"No short videos found via API search for {country_code}.")
                return
            
            logger.info(f"Found {len(unique_video_ids)} unique candidate Shorts for {country_code}. Fetching details...")
            
            # Get full details for these videos (up to 50 at a time)
            video_ids = list(unique_video_ids)[:50]
            details = self.api_client.get_video_details(video_ids)
            
            # Filter to <=60 seconds (true Shorts)
            shorts_items = []
            for item in details:
                duration_str = item.get("contentDetails", {}).get("duration", "")
                seconds = self.parse_iso8601_duration_to_seconds(duration_str)
                if 0 < seconds <= 60:
                    shorts_items.append(item)
            
            if shorts_items:
                await self._process_api_videos(country_code, shorts_items, force_shorts=True)
                logger.info(f"Ingested {len(shorts_items)} Shorts via API search for {country_code}.")
            else:
                logger.info(f"No true Shorts (<=60s) found via API for {country_code}.")
        except Exception as e:
            logger.warning(f"API Shorts search failed for {country_code}: {e}")

    async def _process_api_videos(self, country_code: str, api_items: List[Dict[str, Any]], force_shorts: bool = False) -> None:
        """Process and ingest raw videos fetched from official YouTube API."""
        if not api_items:
            logger.info("No videos found from API.")
            return

        channel_ids = list(set([item["snippet"]["channelId"] for item in api_items]))
        
        # Fetch detailed channel info (subscribers count, total views)
        channels_detail = {}
        try:
            channels_data = self.api_client.get_channel_details(channel_ids)
            for ch in channels_data:
                channels_detail[ch["id"]] = ch
        except Exception as e:
            logger.warning(f"Failed to fetch channel details: {e}. Proceeding with default values.")

        async with AsyncSessionLocal() as session:
            channel_repo = ChannelRepository(session)
            video_repo = VideoRepository(session)
            
            for item in api_items:
                snippet = item["snippet"]
                stats = item["statistics"]
                content_details = item["contentDetails"]
                
                video_id = item["id"]
                channel_id = snippet["channelId"]
                
                # Extract statistics with default values
                views = int(stats.get("viewCount", 0))
                likes = int(stats.get("likeCount", 0))
                comments = int(stats.get("commentCount", 0))
                
                # Fetch Channel stats
                ch_detail = channels_detail.get(channel_id, {})
                ch_stats = ch_detail.get("statistics", {})
                ch_snippet = ch_detail.get("snippet", {})
                
                subscribers = int(ch_stats.get("subscriberCount", 0))
                ch_views = int(ch_stats.get("viewCount", 0))
                ch_videos = int(ch_stats.get("videoCount", 0))
                
                # Create/Merge Channel Model
                channel = Channel(
                    channel_id=channel_id,
                    title=ch_snippet.get("title", snippet.get("channelTitle", "Unknown Channel")),
                    description=ch_snippet.get("description"),
                    custom_url=ch_snippet.get("customUrl"),
                    published_at=self._parse_datetime(ch_snippet.get("publishedAt")),
                    thumbnail_url=ch_snippet.get("thumbnails", {}).get("high", {}).get("url"),
                    view_count=ch_views,
                    subscriber_count=subscribers,
                    video_count=ch_videos,
                    country_code=country_code
                )
                
                # Determine isShort
                tags = snippet.get("tags", [])
                duration_str = content_details.get("duration")
                is_shorts = force_shorts or self.check_is_shorts(duration_str, snippet.get("title", ""), tags)
                
                # For GLOBAL collection, skip videos already saved under a specific country
                # to prevent GLOBAL (which uses regionCode=US) from overwriting US data
                if country_code == "GLOBAL":
                    existing = await video_repo.get_video_with_details(video_id)
                    if existing and existing.country_code != "GLOBAL":
                        logger.debug(f"Skipping video {video_id} for GLOBAL — already saved under {existing.country_code}")
                        continue
                
                # Create/Merge Video Model
                video = Video(
                    video_id=video_id,
                    title=snippet.get("title", ""),
                    description=snippet.get("description", ""),
                    channel_id=channel_id,
                    country_code=country_code,
                    language=snippet.get("defaultAudioLanguage"),
                    publish_time=self._parse_datetime(snippet.get("publishedAt")) or datetime.now(timezone.utc),
                    duration=duration_str,
                    views=views,
                    likes=likes,
                    comments=comments,
                    subscriber=subscribers,
                    thumbnail=snippet.get("thumbnails", {}).get("high", {}).get("url"),
                    tags=tags,
                    category=snippet.get("categoryId"),
                    isShort=is_shorts
                )

                
                # Store data in a clean transaction
                try:
                    await channel_repo.upsert_channel(channel)
                    await video_repo.upsert_video(video)
                except Exception as db_err:
                    logger.error(f"DB Ingestion Error for video {video_id}: {db_err}")
                    await session.rollback()
                    continue

            await session.commit()
            logger.info(f"Ingested {len(api_items)} videos via API.")

    async def _process_scraped_videos(self, country_code: str, scraped_items: List[Dict[str, Any]], is_shorts: bool) -> None:
        """Process and ingest fallback videos scraped via Playwright."""
        if not scraped_items:
            logger.info("No videos found from Playwright scraper.")
            return

        async with AsyncSessionLocal() as session:
            channel_repo = ChannelRepository(session)
            video_repo = VideoRepository(session)
            
            for item in scraped_items:
                video_id = item["video_id"]
                channel_id = item["channel_id"]
                
                # Merge Channel first
                channel = Channel(
                    channel_id=channel_id,
                    title=item["channel_title"],
                    country_code=country_code,
                    subscriber_count=0, # Detail unavailable without API/additional page scraping
                    view_count=0,
                    video_count=0
                )
                
                # Merge Video
                video = Video(
                    video_id=video_id,
                    title=item["title"],
                    channel_id=channel_id,
                    country_code=country_code,
                    views=item["views"],
                    likes=0,       # Fallback mock values
                    comments=0,    # Fallback mock values
                    subscriber=0,  # Fallback mock values
                    thumbnail=item["thumbnail_url"],
                    isShort=is_shorts,
                    publish_time=datetime.now(timezone.utc) # Scrape time approximation
                )
                
                try:
                    await channel_repo.upsert_channel(channel)
                    await video_repo.upsert_video(video)
                except Exception as db_err:
                    logger.error(f"DB Fallback Ingestion Error for video {video_id}: {db_err}")
                    await session.rollback()
                    continue

            await session.commit()
            logger.info(f"Ingested {len(scraped_items)} videos via Playwright Scraper (Shorts={is_shorts}).")

    async def run_pipeline(self) -> None:
        """Main execution loop for all 8 target countries.
        GLOBAL is handled separately: it doesn't re-fetch from API but instead
        the ranking engine aggregates all countries' videos into a GLOBAL ranking."""
        async with AsyncSessionLocal() as session:
            country_repo = CountryRepository(session)
            active_countries = await country_repo.get_active_countries()
        
        country_codes = [c.code for c in active_countries]
        if not country_codes:
            country_codes = ["KR", "US", "JP", "IN", "GB", "CA", "AU", "GLOBAL"]
            logger.warning(f"No active countries found in DB. Falling back to default list: {country_codes}")

        # Remove GLOBAL from collection list — GLOBAL ranking is computed by
        # aggregating all countries' videos in the ranking engine, not by re-crawling.
        country_codes = [c for c in country_codes if c != "GLOBAL"]

        for code in country_codes:
            await self.collect_for_country(code)
            await asyncio.sleep(2.0)
        
        logger.info("All country collections complete. GLOBAL ranking will be computed from aggregated data.")
