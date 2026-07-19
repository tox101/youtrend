import logging
import asyncio
from datetime import datetime, timezone, date

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import joinedload
from models.video import Video
from models.rank import VideoRank, RankingHistory
from models.country import Country

logger = logging.getLogger("ranking.engine")
logging.basicConfig(level=logging.INFO)

class RankingEngine:
    """
    Computes Virality Scores and generates Top 50/100 rankings for Longform & Shorts
    on daily, weekly, and monthly intervals.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    def calculate_virality_score(self, video: Video, period: str = "daily") -> float:
        """
        Calculates raw virality score geared towards content creators.
        Optimized to highlight small channels with high engagement and virality.
        """
        now = datetime.now(timezone.utc)
        publish_time = video.publish_time
        if publish_time.tzinfo is None:
            publish_time = publish_time.replace(tzinfo=timezone.utc)
        age_seconds = (now - publish_time).total_seconds()
        age_hours = max(age_seconds / 3600.0, 0.5)  # Avoid division by zero, min 30 minutes

        # 1. View velocity (Views per hour since uploaded)
        view_velocity = video.views / age_hours

        # 2. Like Rate (with safeguard for zero views)
        like_rate = (video.likes / video.views) if video.views > 0 else 0.0
        
        # 3. Comment Rate (weighted higher to reflect active community engagement)
        comment_rate = (video.comments / video.views) if video.views > 0 else 0.0

        # 4. View to Subscriber ratio (shows explosive growth beyond subscriber base)
        sub_count = video.subscriber if video.subscriber > 0 else 1000  # Default fallback sub
        views_to_sub = video.views / sub_count

        # 5. Time Decay Penalty (weakened for weekly/monthly to surface steady trends)
        if period == "weekly":
            gravity = 0.7
        elif period == "monthly":
            gravity = 0.4
        else:  # daily
            gravity = 1.2
            
        decay_factor = 1.0 / ((age_hours + 2.0) ** gravity)

        # Weights configuration (optimized for creator benchmarking)
        w_sub_ratio = 0.35  # Highlight low sub but high virality (idea validation)
        w_comment = 0.20    # High discussion value
        w_velocity = 0.25   # Lower weight to prevent big channels from dominating
        w_like = 0.20       # Engagement indicator

        # Raw Score calculation
        raw_score = (
            (w_velocity * min(view_velocity / 100.0, 1000.0)) + # Clip extreme velocity
            (w_like * like_rate * 10000.0) +                    # Scaled to comparable magnitudes
            (w_comment * comment_rate * 50000.0) +
            (w_sub_ratio * min(views_to_sub * 100.0, 500.0))
        ) * decay_factor

        return max(raw_score, 0.0)

    async def run_ranking_pipeline_for_country(self, country_code: str) -> None:
        """
        Collects all videos for a specific country, calculates virality scores,
        updates the live ranking charts (Top 100), and appends historical timelines.
        """
        logger.info(f"Running ranking update pipeline for Country: {country_code}")
        
        # 1. Fetch active videos in the country
        # For GLOBAL, aggregate ALL videos across all countries
        if country_code == "GLOBAL":
            video_query = (
                select(Video)
                .options(joinedload(Video.channel))
            )
        else:
            video_query = (
                select(Video)
                .where(Video.country_code == country_code)
                .options(joinedload(Video.channel))
            )
        result = await self.db.execute(video_query)
        videos = list(result.scalars().unique().all())

        if not videos:
            logger.info(f"No videos found for country {country_code}. Skipping ranking calculation.")
            return

        # 2. Split and compute rankings for each period (Daily, Weekly, Monthly)
        # Daily: All active videos
        shorts_daily = []
        longform_daily = []
        for video in videos:
            score = self.calculate_virality_score(video, period="daily")
            item = {"video": video, "raw_score": score}
            if video.isShort:
                shorts_daily.append(item)
            else:
                longform_daily.append(item)
        await self._process_group_ranking(country_code, shorts_daily, is_shorts=True, period="daily")
        await self._process_group_ranking(country_code, longform_daily, is_shorts=False, period="daily")

        # Weekly: Videos published in the last 7 days
        now = datetime.now(timezone.utc)
        def is_recent(v_time, days):
            if v_time.tzinfo is None:
                v_time = v_time.replace(tzinfo=timezone.utc)
            return (now - v_time).days <= days

        shorts_weekly = []
        longform_weekly = []
        for video in videos:
            if is_recent(video.publish_time, 7):
                score = self.calculate_virality_score(video, period="weekly")
                item = {"video": video, "raw_score": score}
                if video.isShort:
                    shorts_weekly.append(item)
                else:
                    longform_weekly.append(item)
        await self._process_group_ranking(country_code, shorts_weekly, is_shorts=True, period="weekly")
        await self._process_group_ranking(country_code, longform_weekly, is_shorts=False, period="weekly")

        # Monthly: Videos published in the last 30 days
        shorts_monthly = []
        longform_monthly = []
        for video in videos:
            if is_recent(video.publish_time, 30):
                score = self.calculate_virality_score(video, period="monthly")
                item = {"video": video, "raw_score": score}
                if video.isShort:
                    shorts_monthly.append(item)
                else:
                    longform_monthly.append(item)
        await self._process_group_ranking(country_code, shorts_monthly, is_shorts=True, period="monthly")
        await self._process_group_ranking(country_code, longform_monthly, is_shorts=False, period="monthly")
        
        await self.db.commit()
        logger.info(f"Finished ranking pipeline for Country: {country_code}")

    async def _process_group_ranking(self, country_code: str, items: List[Dict[str, Any]], is_shorts: bool, period: str = "daily") -> None:
        """Helper to normalize scores, sort, upsert database ranks, and log history."""
        if not items:
            return

        # Sort by raw score descending
        items.sort(key=lambda x: x["raw_score"], reverse=True)

        max_raw = items[0]["raw_score"]
        min_raw = items[-1]["raw_score"]
        raw_range = max_raw - min_raw if max_raw != min_raw else 1.0

        today = date.today()

        # We will update daily/weekly/monthly ranking chart. Top 100 max.
        top_items = items[:100]

        # In order to update current rankings cleanly, delete existing rank records for today and current period
        delete_stmt = (
            delete(VideoRank)
            .where(
                VideoRank.country_code == country_code,
                VideoRank.is_shorts == is_shorts,
                VideoRank.period == period,
                VideoRank.rank_date == today
            )
        )
        await self.db.execute(delete_stmt)

        for i, item in enumerate(top_items, start=1):
            video = item["video"]
            raw_score = item["raw_score"]

            # Normalize to 0-100 scale
            normalized_score = round(((raw_score - min_raw) / raw_range) * 100.0, 2)
            
            # Create Rank record
            rank_record = VideoRank(
                video_id=video.video_id,
                rank=i,
                virality_score=normalized_score,
                is_shorts=is_shorts,
                period=period,
                country_code=country_code,
                rank_date=today,
                updated_at=datetime.utcnow()
            )
            self.db.add(rank_record)

            # Create History timeline record only for Daily rankings to avoid redundancy and key conflicts
            if period == "daily":
                history_record = RankingHistory(
                    video_id=video.video_id,
                    rank=i,
                    virality_score=normalized_score,
                    views=video.views,
                    likes=video.likes,
                    comments=video.comments,
                    country_code=country_code,
                    recorded_at=datetime.utcnow()
                )
                try:
                    self.db.add(history_record)
                    await self.db.flush()
                except Exception as hist_err:
                    self.db.expunge(history_record)
                    logger.warning(f"Skipping history timeline insert due to key collision or issue: {hist_err}")

            # If Virality Score is >= 95 and period is daily, trigger AI analysis + XGBoost prediction + Discord alert
            if period == "daily" and normalized_score >= 95.0:
                logger.info(f"ALERT: Video {video.video_id} ('{video.title[:15]}...') scored a massive Virality Score of {normalized_score}. Processing analysis sequentially...")
                
                # 1. AI Analysis (sequential)
                from services.ai_service import AIService
                ai_service = AIService(self.db)
                try:
                    await ai_service.generate_analysis(video.video_id)
                except Exception as ai_err:
                    logger.error(f"Sequential AI analysis failed: {ai_err}")
                
                # 2. XGBoost 24h Views Prediction (sequential)
                from ranking.prediction_model import VideoViewsPredictor
                predictor = VideoViewsPredictor(self.db)
                try:
                    predicted_views, confidence = await predictor.predict_24h_views(video)
                    logger.info(f"XGBoost Prediction for {video.video_id}: 24h Views={predicted_views:,} (Confidence={confidence:.0%})")
                except Exception as pred_err:
                    logger.error(f"Sequential XGBoost prediction failed: {pred_err}")
                
                # 3. Discord Webhook Alert (non-blocking, safe as it doesn't access DB session)
                from utils.notifier import send_discord_alert
                asyncio.create_task(send_discord_alert(
                    video_title=video.title,
                    video_id=video.video_id,
                    score=normalized_score,
                    alert_type="VIRALITY",
                    thumbnail_url=video.thumbnail,
                    views=video.views
                ))

    async def _run_prediction(self, predictor, video) -> None:
        """Helper to run XGBoost prediction and log result."""
        try:
            predicted_views, confidence = await predictor.predict_24h_views(video)
            logger.info(
                f"XGBoost Prediction for {video.video_id}: "
                f"24h Views={predicted_views:,} (Confidence={confidence:.0%})"
            )
        except Exception as e:
            logger.error(f"XGBoost prediction failed for {video.video_id}: {e}")



    async def run_global_pipeline(self) -> None:
        """Runs the rank computation pipeline across all active countries."""
        country_query = select(Country).where(Country.is_active == True)
        result = await self.db.execute(country_query)
        countries = result.scalars().all()

        for country in countries:
            try:
                await self.run_ranking_pipeline_for_country(country.code)
            except Exception as e:
                logger.error(f"Failed to process ranking for country {country.code}: {e}", exc_info=True)
