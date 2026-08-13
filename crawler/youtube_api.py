import os
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

class YouTubeQuotaExceededException(Exception):
    """Custom exception raised when YouTube API quota is exceeded."""
    pass

class YouTubeAPIClient:
    """
    Wrapper for YouTube Data API v3 to fetch trending videos and channel statistics.
    Implements rate limit detection to fall back gracefully.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("YouTube API key is missing. Set YOUTUBE_API_KEY in .env file.")
        
        # Build the youtube service resource
        self.youtube = build("youtube", "v3", developerKey=self.api_key)

    def is_quota_error(self, error: HttpError) -> bool:
        """Check if the HTTP error represents a quota limit exceeded error."""
        if error.resp.status in (403, 429):
            content = error.content.decode("utf-8") if isinstance(error.content, bytes) else str(error.content)
            if any(term in content for term in ("quotaExceeded", "limitExceeded", "rateLimitExceeded")):
                return True
        return False

    def get_trending_videos(self, country_code: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch trending videos for a specific country code.
        Supports pageToken pagination to retrieve more than 50 videos.
        """
        region_code = country_code if country_code != "GLOBAL" else "US"
        items = []
        next_page_token = None
        
        while len(items) < max_results:
            results_to_fetch = min(max_results - len(items), 50)
            try:
                request = self.youtube.videos().list(
                    part="id,snippet,contentDetails,statistics",
                    chart="mostPopular",
                    regionCode=region_code,
                    maxResults=results_to_fetch,
                    pageToken=next_page_token
                )
                response = request.execute()
                items.extend(response.get("items", []))
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
            except HttpError as e:
                if self.is_quota_error(e):
                    raise YouTubeQuotaExceededException("YouTube API Quota exceeded while fetching trending videos.")
                raise e
        return items

    def get_video_details(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch detailed statistics and snippet metadata for a list of video IDs."""
        if not video_ids:
            return []
        
        # API accepts up to 50 video IDs per request
        results = []
        chunks = [video_ids[i:i + 50] for i in range(0, len(video_ids), 50)]
        
        for chunk in chunks:
            try:
                request = self.youtube.videos().list(
                    part="id,snippet,contentDetails,statistics",
                    id=",".join(chunk)
                )
                response = request.execute()
                results.extend(response.get("items", []))
            except HttpError as e:
                if self.is_quota_error(e):
                    raise YouTubeQuotaExceededException("YouTube API Quota exceeded while fetching video details.")
                raise e
        return results

    def get_channel_details(self, channel_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch detailed statistics for a list of channel IDs (e.g., subscriber counts)."""
        if not channel_ids:
            return []
        
        results = []
        chunks = [channel_ids[i:i + 50] for i in range(0, len(channel_ids), 50)]
        
        for chunk in chunks:
            try:
                request = self.youtube.channels().list(
                    part="id,snippet,statistics",
                    id=",".join(chunk)
                )
                response = request.execute()
                results.extend(response.get("items", []))
            except HttpError as e:
                if self.is_quota_error(e):
                    raise YouTubeQuotaExceededException("YouTube API Quota exceeded while fetching channel details.")
                raise e
        return results
