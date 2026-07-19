import logging
import numpy as np
from datetime import datetime, timezone
from typing import Tuple, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.video import Video

# Try importing ML dependencies. Fallback to math model if library build is still running
try:
    import xgboost as xgb
    from sklearn.preprocessing import MinMaxScaler
    HAS_ML_LIBS = True
except ImportError:
    HAS_ML_LIBS = False

logger = logging.getLogger("ranking.prediction_model")
logging.basicConfig(level=logging.INFO)

class VideoViewsPredictor:
    """
    XGBoost-based predictor estimating 24-hour cumulative views for trending videos.
    Extracts features like view velocity, age, like/comment ratios, and short form flags.
    Automatically self-trains on DB history, falling back to a mathematical projection
    during cold-start phases.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    def _extract_features(self, video: Video, age_hours: float) -> np.ndarray:
        """Extracts standard ML feature array for a single video."""
        velocity = video.views / age_hours if age_hours > 0 else 0
        like_ratio = video.likes / video.views if video.views > 0 else 0
        comment_ratio = video.comments / video.views if video.views > 0 else 0
        is_shorts = 1.0 if video.isShort else 0.0

        # Feature Vector: [views, velocity, like_ratio, comment_ratio, age_hours, is_shorts]
        return np.array([video.views, velocity, like_ratio, comment_ratio, age_hours, is_shorts], dtype=float)

    async def _build_training_dataset(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Queries historical video records from DB to construct X, y dataset for training."""
        query = select(Video).limit(500) # Fetch up to 500 records to prevent DB memory exhaust
        result = await self.db.execute(query)
        videos = result.scalars().all()

        if len(videos) < 15: # Require at least 15 videos to train a stable model
            return None, None

        X_list = []
        y_list = []
        now = datetime.now(timezone.utc)

        for v in videos:
            publish_time = v.publish_time
            if publish_time.tzinfo is None:
                publish_time = publish_time.replace(tzinfo=timezone.utc)
            age_hours = (now - publish_time).total_seconds() / 3600.0
            if age_hours < 1.0:
                continue
            
            features = self._extract_features(v, age_hours)
            # Target (Y) value is the cumulative views. We scale and predict the growth factor.
            # In production, Y would be actual views captured at precisely T=24 hours.
            # For self-training approximation, we model current views as the target relative to duration.
            X_list.append(features)
            y_list.append(v.views)

        if not X_list:
            return None, None

        return np.array(X_list), np.array(y_list)

    def _math_projection_fallback(self, video: Video, age_hours: float) -> int:
        """Mathematical logarithmic growth projection used when training data is scarce."""
        # Simple projection: views_24h = current_views * (24 / current_age) ^ alpha
        # Alpha is growth decay exponent (typically 0.6 for viral videos)
        if age_hours >= 24.0:
            return video.views
            
        ratio = 24.0 / max(age_hours, 0.5)
        alpha = 0.55 if video.isShort else 0.65 # Shorts decay faster
        projected = int(video.views * (ratio ** alpha))
        return max(projected, video.views)

    async def predict_24h_views(self, video: Video) -> Tuple[int, float]:
        """
        Predicts the 24-hour total views and confidence score for a video.
        Self-trains an XGBoost model on the fly if DB contains enough video samples.
        """
        now = datetime.now(timezone.utc)
        publish_time = video.publish_time
        if publish_time.tzinfo is None:
            publish_time = publish_time.replace(tzinfo=timezone.utc)
        age_hours = max((now - publish_time).total_seconds() / 3600.0, 0.5)

        # 1. Cold-start check (Check if ML libraries are ready and DB has training dataset)
        if not HAS_ML_LIBS:
            logger.warning("ML libraries (xgboost/scikit-learn) not imported. Falling back to math model.")
            predicted_views = self._math_projection_fallback(video, age_hours)
            return predicted_views, 0.50 # Baseline confidence

        try:
            X_train, y_train = await self._build_training_dataset()
            
            if X_train is None or len(X_train) < 15:
                # Fallback to mathematical projection during startup
                logger.info(f"Insufficient dataset ({0 if X_train is None else len(X_train)} samples) to train XGBoost. Using math fallback.")
                predicted_views = self._math_projection_fallback(video, age_hours)
                return predicted_views, 0.60 # Standard baseline confidence

            # 2. Extract features for target video
            target_features = self._extract_features(video, age_hours).reshape(1, -1)

            # 3. Fit XGBoost Regressor
            scaler = MinMaxScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            target_features_scaled = scaler.transform(target_features)

            # Define ultra-lightweight booster to prevent overhead
            model = xgb.XGBRegressor(
                n_estimators=30,
                max_depth=3,
                learning_rate=0.1,
                objective="reg:squarederror",
                random_state=42
            )
            model.fit(X_train_scaled, y_train)

            # 4. Predict
            prediction = model.predict(target_features_scaled)
            predicted_views = int(prediction[0])
            
            # Bound prediction so it's not less than current views
            predicted_views = max(predicted_views, video.views)

            # Generate confidence score based on dataset size and age limits (Closer to 24h is higher confidence)
            dataset_factor = min(len(X_train) / 100.0, 1.0) * 0.2
            proximity_factor = min(age_hours / 24.0, 1.0) * 0.7
            confidence = round(0.1 + dataset_factor + proximity_factor, 2)
            
            return predicted_views, min(confidence, 0.99)

        except Exception as err:
            logger.error(f"Error in XGBoost prediction pipeline: {err}. Using math fallback.", exc_info=True)
            predicted_views = self._math_projection_fallback(video, age_hours)
            return predicted_views, 0.50
