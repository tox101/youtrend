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
        # YouTube API 클라이언트 — 키가 없거나 무효하면 Playwright 전용 모드로 동작
        try:
            self.api_client = YouTubeAPIClient(api_key=api_key)
        except Exception as e:
            logger.warning(f"YouTube API client unavailable ({e}). Running in Playwright-only mode.")
            self.api_client = None
        # Playwright 스크래퍼 — 브라우저 미설치 환경에서는 API 전용 모드로 동작
        try:
            self.scraper = PlaywrightScraper(headless=True)
        except Exception as e:
            logger.warning(f"Playwright scraper unavailable ({e}). Running in API-only mode.")
            self.scraper = None

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

    def classify_age(self, title: str, description: Optional[str], tags: Optional[List[str]] = None) -> str:
        import hashlib
        title_lower = title.lower()
        desc_lower = (description or "").lower()
        tag_str = " ".join(tags or []).lower()
        text = f"{title_lower} {desc_lower} {tag_str}"
        
        # 1. Gaming / Anime / Roblox / Chzzk exclusions → Defaults to "40대" (youngest active cohort)
        game_keywords = [
            "게임", "game", "gaming", "포켓몬", "pokemon", "리그오브레전드", "롤", "lol", "배그", "pubg", 
            "오버워치", "피파", "fc온라인", "마인크래프트", "minecraft", "스팀게임", "치지직", 
            "chzzk", "아프리카tv", "스트리머", "비제이", "bj", "애니메이션", "덕질", "버튜버", 
            "로블록스", "roblox", "fortnite", "valorant", "call of duty", "gta", "fps", "rpg",
            "esports", "twitch", "streamer", "playthrough", "walkthrough", "speedrun"
        ]
        if any(kw in text for kw in game_keywords):
            return "40대"  # Default to youngest cohort on platform
        
        # 60대 이상 — Korean keywords
        score_60 = 0
        keywords_60_kr = [
            "임영웅", "송가인", "트로트", "장민호", "이찬원", "김호중", "영탁", "정동원", "남진", "나훈아", 
            "주현미", "심수봉", "설운도", "태진아", "송대관", "장윤정", "홍진영", "김연자", "진성", "박군",
            "가요무대", "전국노래자랑", "가요 백과", "가요 대백과", "옛가요", "7080", "옛날 노래", "포크송", 
            "건강상식", "관절", "치매", "고혈압", "당뇨", "노후", "은퇴", "백세", "시니어", "노인", 
            "황혼", "아침마당", "텃밭", "건강 정보", "혈관", "골다공증", "요실금", "임플란트", "보청기",
            "불교", "스님", "법문", "기독교", "목사", "예배", "찬송가", "성경", "천주교", "신부님",
            "정치 시사", "보수 뉴스", "진보 뉴스", "대통령", "국회", "선거", "정치인", "시청", "구청",
            "민원", "틀니", "상조", "실버타운", "손주", "손자", "손녀", "약초", "민간요법"
        ]
        # 60대 이상 — English keywords
        keywords_60_en = [
            "senior", "elderly", "grandparent", "grandmother", "grandfather", "retirement",
            "medicare", "social security", "pension", "arthritis", "dementia", "alzheimer",
            "memory care", "assisted living", "nursing home", "over 60", "over 65", "over 70",
            "golden years", "senior fitness", "senior health", "aging", "longevity",
            "blood pressure", "diabetes management", "osteoporosis", "hearing aid",
            "trot", "oldies", "nostalgia", "buddhism", "christianity", "hymn", "sermon",
            "politics", "conservative", "progressive", "news analysis"
        ]
        for kw in keywords_60_kr + keywords_60_en:
            if kw in text:
                score_60 += 3
                
        # 50대 — Korean keywords
        score_50 = 0
        keywords_50_kr = [
            "은퇴 준비", "부동산 전망", "주식 시장", "노후 준비", "50대", "중년", "등산", "약초", 
            "갱년기", "건강 보조", "골프", "요리 레시피", "시사", "정치", "역사", "인문학", "재테크",
            "캠핑카", "주말농장", "낚시", "경매", "세금", "상속", "증여", "건강검진", "콜레스테롤", 
            "영양제", "비타민", "중년 건강", "은퇴 증후군", "귀농", "귀촌", "8090", "통기타",
            "산악회", "둘레길", "트레킹", "등산코스", "바둑", "장기"
        ]
        # 50대 — English keywords
        keywords_50_en = [
            "retirement planning", "real estate", "investment", "financial planning",
            "over 50", "50s", "midlife", "menopause", "empty nester", "empty nest",
            "golf", "gardening", "wine tasting", "travel tips", "cruise", 
            "wealth management", "401k", "ira", "estate planning", "college fund",
            "career change", "second career", "downsizing", "home equity",
            "hiking", "fishing", "camping car", "weekend farm", "health checkup"
        ]
        for kw in keywords_50_kr + keywords_50_en:
            if kw in text:
                score_50 += 2

        # 40대 — Korean keywords
        score_40 = 0
        keywords_40_kr = [
            "재테크", "부동산", "아파트", "육아", "초등", "자녀 교육", "캠핑", "자동차", 
            "직장인", "승진", "마흔", "40대", "건강", "피트니스", "밀키트", "자기계발", 
            "영어 회화", "부업", "창업", "쇼핑", "패션", "fashion", "뷰티", "스타일", 
            "style", "마케팅", "인플루언서", "주얼리", "다이어트"
        ]
        # 40대 — English keywords
        keywords_40_en = [
            "parenting", "mom", "dad", "toddler", "elementary school", "back to school",
            "work life balance", "corporate", "career growth", "promotion", "leadership",
            "mortgage", "home buying", "home improvement", "diy", "renovation",
            "camping", "suv", "road trip", "fitness", "weight loss", "meal prep",
            "side hustle", "entrepreneurship", "startup", "productivity", "self improvement",
            "budgeting", "saving money", "personal finance", "credit score",
            "skincare routine", "anti-aging", "beauty", "fashion tips", "wardrobe"
        ]
        for kw in keywords_40_kr + keywords_40_en:
            if kw in text:
                score_40 += 2
                
        max_score = max(score_40, score_50, score_60)
        # If no keyword matched at all, return "all" — this is non-classified content
        if max_score == 0:
            return "all"
            
        if max_score == score_60 and score_60 > score_50 and score_60 > score_40:
            return "60대이상"
        elif max_score == score_50 and score_50 > score_40:
            return "50대"
        else:
            return "40대"


    def classify_gender(self, title: str, description: Optional[str], tags: Optional[List[str]] = None) -> str:
        """Classify target gender based on title + description keywords."""
        import re
        title_lower = title.lower()
        desc_lower = (description or "").lower()
        tag_str = " ".join(tags or []).lower()
        text = f"{title_lower} {desc_lower} {tag_str}"
        
        # Exclude karaoke / music cover channels
        karaoke_keywords = ["노래방", "karaoke", "금영", "tj미디어", "태진"]
        if any(kw in text for kw in karaoke_keywords):
            return "공통"
        
        score_female = 0
        score_male = 0
        
        # Regex patterns for female targeting
        patterns_female = [
            r"뷰티", r"메이크업", r"화장(?!대)", r"스킨케어", r"피부", r"(?<!썸)네일", r"다이어트",
            r"요가", r"필라테스", r"패션", r"코디", r"쇼핑", r"하울", r"언박싱",
            r"육아", r"임신", r"출산", r"베이비", r"아기", r"엄마", r"레시피",
            r"요리", r"베이킹", r"디저트", r"홈카페", r"인테리어", r"집꾸미기",
            r"로맨스", r"드라마", r"감성", r"힐링", r"명상", r"asmr",
            r"beauty", r"makeup", r"skincare", r"fashion", r"haul", r"yoga",
            r"pilates", r"recipe", r"cooking", r"baking", r"vlog", r"브이로그",
            r"grwm", r"꿀팁", r"셀프(?!카)", r"웨딩",
            r"살림", r"반찬", r"주부", r"가계부", r"뜨개질", r"자수", r"원예", r"꽃꽂이",
            r"밑반찬", r"가정식"
        ]
        # Match '맘' but not '맘대로' or '맘스터치'
        if re.search(r"\b맘\b|(?<!제 )맘(?!대로)(?!스터치)", text):
            score_female += 2

        for pattern in patterns_female:
            if re.search(pattern, text):
                score_female += 2
        
        # Regex patterns for male targeting
        patterns_male = [
            r"게임", r"리그오브레전드", r"배틀그라운드", r"오버워치", r"fps",
            r"자동차", r"슈퍼카", r"바이크", r"오토바이", r"튜닝", r"드라이브",
            r"축구", r"야구", r"농구", r"격투기", r"복싱", r"mma", r"ufc",
            r"헬스", r"벌크업", r"근육", r"운동", r"웨이트", r"크로스핏",
            r"밀리터리", r"군사", r"무기", r"전쟁", r"서바이벌", r"낚시",
            r"코딩", r"프로그래밍", r"개발자", r"(?<!재)테크", r"\bit\b",
            r"주식(?!회사)", r"코인", r"비트코인", r"투자", r"경제",
            r"gaming", r"game", r"car", r"sports", r"football", r"soccer",
            r"basketball", r"boxing", r"workout", r"gym", r"tech", r"crypto",
            r"bitcoin", r"stock", r"trading", r"전략", r"리뷰"
        ]
        for pattern in patterns_male:
            if re.search(pattern, text):
                score_male += 2
        
        if score_female > score_male:
            return "여성"
        elif score_male > score_female:
            return "남성"
        else:
            return "공통"

    async def collect_for_country(self, country_code: str) -> None:
        """
        Collects trending videos (Longform and Shorts) for a given country.
        Gracefully switches to Playwright if API Quota is exceeded.
        """
        logger.info(f"=== Starting collection for Country: {country_code} ===")
        
        # 1. Collect Longform / Standard Trending
        if self.api_client is not None:
            try:
                logger.info("Fetching trending via YouTube API...")
                api_videos = self.api_client.get_trending_videos(country_code, max_results=100)
                await self._process_api_videos(country_code, api_videos)
            except YouTubeQuotaExceededException:
                logger.warning("YouTube API Quota exceeded. Falling back to Playwright Scraper for Longform.")
                if self.scraper is not None:
                    scraped_videos = await self.scraper.scrape_trending(country_code, is_shorts=False, limit=50)
                    await self._process_scraped_videos(country_code, scraped_videos, is_shorts=False)
                else:
                    logger.warning("Playwright scraper unavailable — skipping Longform fallback.")
            except Exception as e:
                logger.error(f"Failed to collect API videos for {country_code}: {e}", exc_info=True)
                # Try Playwright fallback anyways on unexpected API error
                if self.scraper is not None:
                    try:
                        scraped_videos = await self.scraper.scrape_trending(country_code, is_shorts=False, limit=50)
                        await self._process_scraped_videos(country_code, scraped_videos, is_shorts=False)
                    except Exception as pe:
                        logger.error(f"Playwright fallback also failed for {country_code}: {pe}")
                else:
                    logger.error(f"Playwright scraper unavailable — cannot fallback for {country_code}.")
        elif self.scraper is not None:
            # API 키 없음 → Playwright로만 Longform 수집
            logger.info("YouTube API unavailable. Collecting Longform via Playwright only.")
            try:
                scraped_videos = await self.scraper.scrape_trending(country_code, is_shorts=False, limit=50)
                await self._process_scraped_videos(country_code, scraped_videos, is_shorts=False)
            except Exception as e:
                logger.error(f"Playwright-only Longform collection failed for {country_code}: {e}")
        else:
            logger.error("No crawler source available for Longform (API & Playwright both disabled).")
        
        # 2. Collect Shorts Trending
        if self.scraper is not None:
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
        elif self.api_client is not None:
            try:
                logger.info("Playwright unavailable. Collecting Shorts via YouTube API only.")
                await self._collect_shorts_via_api(country_code)
            except Exception as e:
                logger.error(f"API-only Shorts collection failed for {country_code}: {e}")
        else:
            logger.error("No crawler source available for Shorts (API & Playwright both disabled).")

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
                    isShort=is_shorts,
                    target_age=self.classify_age(snippet.get("title", ""), snippet.get("description", "")),
                    target_gender=self.classify_gender(snippet.get("title", ""), snippet.get("description", ""))
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
                    publish_time=datetime.now(timezone.utc), # Scrape time approximation
                    target_age=self.classify_age(item["title"], ""),
                    target_gender=self.classify_gender(item["title"], "")
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
