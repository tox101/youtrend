import logging
import asyncio
import time
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright, Page, BrowserContext

logger = logging.getLogger("crawler.playwright_scraper")
logging.basicConfig(level=logging.INFO)

class PlaywrightScraper:
    """
    Playwright-based YouTube scraper configured synchronously to completely bypass
    Windows asyncio event loop limitations (NotImplementedError).
    Exposes an async interface for clean pipeline integration using asyncio.to_thread.
    """
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"

    def _setup_context(self, playwright) -> BrowserContext:
        browser = playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--lang=en-US"
            ]
        )
        context = browser.new_context(
            user_agent=self.user_agent,
            viewport={"width": 1280, "height": 800},
            locale="en-US"
        )
        return context

    async def scrape_trending(
        self, country_code: str, is_shorts: bool = False, limit: int = 50, retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Asynchronous wrapper that delegates the synchronous scraping logic to a
        background threadpool. Returns empty list gracefully upon Windows OS loop errors.
        """
        try:
            return await asyncio.to_thread(
                self._scrape_trending_sync, country_code, is_shorts, limit, retries
            )
        except Exception as e:
            logger.warning(f"Playwright execution skipped due to Windows loop compatibility limit: {e}")
            return []


    def _scrape_trending_sync(
        self, country_code: str, is_shorts: bool, limit: int, retries: int
    ) -> List[Dict[str, Any]]:
        """Synchronous scraper implementation running safely in a separate thread."""
        region = country_code if country_code != "GLOBAL" else "US"
        
        # Shorts page vs Longform trending feed
        if is_shorts:
            url = f"https://www.youtube.com/hashtag/shorts?gl={region}&hl=en"
        else:
            url = f"https://www.youtube.com/feed/trending?gl={region}&hl=en"

        for attempt in range(1, retries + 1):
            try:
                logger.info(f"[Sync Thread Scraper] Scraping attempt {attempt}/{retries} for {country_code} (Shorts={is_shorts})...")
                with sync_playwright() as p:
                    context = self._setup_context(p)
                    page = context.new_page()
                    
                    # Prevent images/stylesheets load for performance & speed optimization
                    page.route("**/*.{png,jpg,jpeg,gif,webp,css,woff,woff2}", lambda route: route.abort())
                    
                    # Navigate with timeout
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Wait for items to load
                    selector = "ytd-video-renderer, ytd-rich-item-renderer"
                    page.wait_for_selector(selector, timeout=15000)
                    
                    # Auto scroll down to fetch more items if needed
                    self._scroll_page_sync(page, scrolls=3)
                    
                    # Parse contents
                    videos = self._parse_videos_sync(page, is_shorts, limit)
                    
                    # Close resources
                    context.browser.close()
                    
                    if videos:
                        logger.info(f"Successfully scraped {len(videos)} videos on attempt {attempt}")
                        return videos
                    else:
                        logger.warning(f"No videos parsed on attempt {attempt}, retrying...")
            except Exception as e:
                logger.error(f"Error on attempt {attempt} for {country_code}: {e}")
                if attempt == retries:
                    raise e
                time.sleep(2 * attempt)
        
        return []

    def _scroll_page_sync(self, page: Page, scrolls: int) -> None:
        """Synchronously scroll page to lazy load metadata."""
        for _ in range(scrolls):
            page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(1.5)

    def _parse_videos_sync(self, page: Page, is_shorts: bool, limit: int) -> List[Dict[str, Any]]:
        """Synchronously parses video elements from DOM."""
        parsed_items = []
        
        if is_shorts:
            items = page.query_selector_all("ytd-rich-item-renderer")
        else:
            items = page.query_selector_all("ytd-video-renderer")

        for item in items:
            if len(parsed_items) >= limit:
                break
                
            try:
                # Video Title & Link
                title_el = item.query_selector("a#video-title, #video-title-link")
                if not title_el:
                    continue
                
                title = title_el.inner_text().strip()
                href = title_el.get_attribute("href")
                if not href:
                    continue
                
                # Extract Video ID
                video_id = ""
                if "v=" in href:
                    video_id = href.split("v=")[1].split("&")[0]
                elif "/shorts/" in href:
                    video_id = href.split("/shorts/")[1].split("?")[0]
                else:
                    continue

                # Channel metadata
                channel_el = item.query_selector("ytd-channel-name a, #channel-info a")
                channel_title = "Unknown Channel"
                channel_id = ""
                if channel_el:
                    channel_title = channel_el.inner_text().strip()
                    channel_href = channel_el.get_attribute("href")
                    if channel_href:
                        channel_id = channel_href.split("/")[-1]

                # Stats (Views and uploaded time)
                metadata_items = item.query_selector_all("#metadata-line span.inline-metadata-item")
                views_str = "0 views"
                publish_time_str = "Unknown"
                
                if len(metadata_items) >= 1:
                    views_str = metadata_items[0].inner_text()
                if len(metadata_items) >= 2:
                    publish_time_str = metadata_items[1].inner_text()

                views = self._clean_views(views_str)

                parsed_items.append({
                    "video_id": video_id,
                    "title": title,
                    "views": views,
                    "channel_title": channel_title,
                    "channel_id": channel_id,
                    "isShort": is_shorts,
                    "published_str": publish_time_str
                })
            except Exception as ex:
                logger.debug(f"Failed parsing singular video element: {ex}")
                
        return parsed_items

    def _clean_views(self, views_str: str) -> int:
        """Parses views string e.g. '1.2M views' into integer."""
        views_str = views_str.lower().replace("views", "").replace("조회수", "").replace("회", "").strip()
        try:
            if "k" in views_str or "천" in views_str:
                return int(float(views_str.replace("k", "").replace("천", "").strip()) * 1000)
            if "m" in views_str or "백만" in views_str:
                return int(float(views_str.replace("m", "").replace("백만", "").strip()) * 1_000_000)
            if "b" in views_str or "십억" in views_str:
                return int(float(views_str.replace("b", "").replace("십억", "").strip()) * 1_000_000_000)
            if "만" in views_str:
                return int(float(views_str.replace("만", "").strip()) * 10000)
            if "억" in views_str:
                return int(float(views_str.replace("억", "").strip()) * 100_000_000)
            # Remove punctuation
            cleaned = "".join([c for c in views_str if c.isdigit()])
            return int(cleaned) if cleaned else 0
        except ValueError:
            return 0
