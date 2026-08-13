import os
import logging
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository import AnalysisRepository, VideoRepository
from models.analysis import AIAnalysis
from models.interaction import Comment

logger = logging.getLogger("services.ai_service")
logging.basicConfig(level=logging.INFO)

class AIService:
    """
    Business logic coordinator for AI Analysis.
    Integrates with LM Studio (Qwen AgentWorld 35B) using OpenAI-compatible API.
    Implements strict caching in PostgreSQL database.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analysis_repo = AnalysisRepository(db)
        self.video_repo = VideoRepository(db)

    async def get_cached_analysis(self, video_id: str) -> Optional[AIAnalysis]:
        """Fetch cached analysis if it exists in DB."""
        return await self.analysis_repo.get_ai_analysis(video_id)

    def _truncate_text(self, text: str, max_chars: int = 500) -> str:
        """Safely truncates long text fields to prevent Qwen context overflow."""
        if not text:
            return ""
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "... (이하 생략)"

    def _build_prompt(self, video: Any, comments: List[Comment], velocity: float) -> str:
        """
        Constructs a structured prompt optimized for Qwen AgentWorld 35B.
        - Truncates description to 500 chars to stay within 4K token budget.
        - Limits to 5 comments with 200 char cap each.
        - Uses explicit section markers for reliable parsing.
        """
        # Truncate video description to prevent token overflow
        safe_description = self._truncate_text(video.description, 500) or "설명 없음"
        
        # Truncate and limit comments
        if comments:
            safe_comments = "\n".join([
                f"- {self._truncate_text(c.text, 200)}" for c in comments[:5]
            ])
        else:
            safe_comments = "댓글 없음"
        
        prompt = f"""[유튜브 영상 메타데이터]
- 제목: {video.title}
- 설명: {safe_description}
- 조회수: {video.views:,}회
- 좋아요: {video.likes:,}개
- 댓글 수: {video.comments:,}개
- 실시간 증가 속도: 시간당 {velocity:.1f}회 조회 증가
- 주요 시청자 댓글 일부:
{safe_comments}

위 데이터를 기반으로 다음 6가지 항목에 대해 명확하고 논리적인 보고서를 한국어로 작성해주세요.
각 항목 사이에는 반드시 명확하게 '[구분자]'를 표기해야 파싱이 가능합니다. 아래 형식과 구분자를 엄격히 지켜주세요.


[WHY_POPULAR]
왜 인기인가 (구체적 분석)
[KEY_FACTORS]
핵심 성공요인 (리스트업)
[TARGET_AUDIENCE]
예상 시청자 (연령, 성향 등)
[SIMILAR_CONTENT]
유사 콘텐츠 (장르 및 참고 채널)
[PREDICTION_24H]
24시간 예측 (조회수 추이 예측)
[IMPROVEMENT]
개선 아이디어 (피드백 제안)
"""
        return prompt

    def _parse_ai_response(self, text: str, video_id: str) -> AIAnalysis:
        """Parses the formatted text output from Qwen model into AIAnalysis model."""
        sections = {
            "why_popular": "",
            "key_success_factors": "",
            "target_audience": "",
            "similar_contents": "",
            "prediction_24h": "",
            "improvement_ideas": ""
        }

        # Helper keys mapping to target DB fields
        keys_map = [
            ("[WHY_POPULAR]", "why_popular"),
            ("[KEY_FACTORS]", "key_success_factors"),
            ("[TARGET_AUDIENCE]", "target_audience"),
            ("[SIMILAR_CONTENT]", "similar_contents"),
            ("[PREDICTION_24H]", "prediction_24h"),
            ("[IMPROVEMENT]", "improvement_ideas")
        ]

        current_key = None
        lines = text.split("\n")
        
        for line in lines:
            line_stripped = line.strip()
            found_header = False
            for header, key in keys_map:
                if header in line_stripped:
                    current_key = key
                    found_header = True
                    break
            
            if found_header:
                continue
                
            if current_key:
                sections[current_key] += line + "\n"

        # Fallback values if parsing failed
        for k in sections:
            sections[k] = sections[k].strip()
            if not sections[k]:
                sections[k] = "분석 데이터를 파싱하지 못했습니다. 상세 메타데이터를 확인해주세요."

        return AIAnalysis(
            video_id=video_id,
            why_popular=sections["why_popular"],
            key_success_factors=sections["key_success_factors"],
            target_audience=sections["target_audience"],
            similar_contents=sections["similar_contents"],
            prediction_24h=sections["prediction_24h"],
            improvement_ideas=sections["improvement_ideas"],
            analyzed_at=datetime.now(timezone.utc)
        )

    async def _build_fallback_analysis(self, video_id: str, video: Any, velocity: float) -> AIAnalysis:
        """Builds and persists a default mock analysis to keep the system alive
        when the AI provider is unreachable (e.g. cloud deployment without LM Studio)."""
        fallback_mock = AIAnalysis(
            video_id=video_id,
            why_popular=f"영상 '{video.title}'은(는) 조회 속도가 시간당 {velocity:.1f}회에 이를 만큼 화제성을 입증했습니다. 시청자의 높은 상호작용율(좋아요 {video.likes:,}개)이 주요 동력입니다.",
            key_success_factors="1. 직관적인 연출 및 가독성 높은 제목\n2. 트렌드 키워드 결합\n3. 초기 트래픽 유입 속도 가속화",
            target_audience="유튜브 급상승 차트를 소비하는 일반 대중 및 트렌드 민감층",
            similar_contents="최신 트렌드 리스트 내 유사 카테고리 급상승 영상",
            prediction_24h="현재 속도 유지 시 24시간 내 조회수가 추가 상승할 가능성이 매우 큽니다.",
            improvement_ideas="구독자 유도를 위해 영상 설명 부분의 링크 구조와 카드 안내를 추가할 것을 권장합니다.",
            analyzed_at=datetime.now(timezone.utc)
        )
        try:
            await self.analysis_repo.save_ai_analysis(fallback_mock)
            await self.db.commit()
            return fallback_mock
        except Exception as db_err:
            await self.db.rollback()
            cached = await self.get_cached_analysis(video_id)
            if cached:
                logger.info(f"AI Cache Hit (after fallback conflict): Returning saved analysis for video {video_id}")
                return cached
            logger.error(f"DB Error saving fallback AI analysis: {db_err}")
            return fallback_mock

    async def generate_analysis(self, video_id: str) -> AIAnalysis:
        """
        Triggers AI analysis.
        Checks cache -> Calls LM Studio -> Parses results -> Caches response in DB.
        """
        # 1. Strict Caching check
        cached = await self.get_cached_analysis(video_id)
        if cached:
            logger.info(f"AI Cache Hit: Returning saved analysis for video {video_id}")
            return cached

        # 2. Retrieve video details and recent comments
        video = await self.video_repo.get_video_with_details(video_id)
        if not video:
            raise ValueError(f"Video {video_id} not found in database.")

        # Calculate view velocity
        now = datetime.now(timezone.utc)
        publish_time = video.publish_time
        if publish_time.tzinfo is None:
            publish_time = publish_time.replace(tzinfo=timezone.utc)
        age_hours = max((now - publish_time).total_seconds() / 3600.0, 0.5)
        velocity = video.views / age_hours

        # Fetch comments linked to the video
        comments = video.comments_list or []

        # 3. Request analysis from local LM Studio Qwen Model
        # 클라우드 배포 환경(Render)에서는 로컬 LM Studio에 접근할 수 없으므로,
        # AI_PROVIDER=disabled 로 설정하면 즉시 fallback 분석을 반환합니다.
        provider = os.getenv("AI_PROVIDER", "lm_studio").strip().lower()
        if provider in ("disabled", "none", "off"):
            logger.info(f"AI_PROVIDER={provider} — skipping external model call; using fallback analysis for video {video_id}.")
            return await self._build_fallback_analysis(video_id, video, velocity)

        api_base = os.getenv("LM_STUDIO_API_BASE", "http://localhost:1234/v1")
        model_name = os.getenv("AI_MODEL_NAME", "Qwen AgentWorld 35B A3B UD")
        
        prompt = self._build_prompt(video, comments, velocity)
        
        logger.info(f"Calling local LM Studio ({model_name}) at {api_base} for video {video_id}...")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{api_base}/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": model_name,
                        "messages": [
                            {
                                "role": "system",
                                "content": "너는 유튜브 바이럴 요소와 급상승 알고리즘을 정량/정성적으로 진단하는 비즈니스 분석 전문가이다. 주어진 규격 필드를 지켜 정중하고 디테일하게 응답하라."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.2
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    analysis = self._parse_ai_response(content, video_id)
                    try:
                        await self.analysis_repo.save_ai_analysis(analysis)
                        await self.db.commit()
                        logger.info(f"Successfully generated and cached AI analysis for video {video_id}.")
                        return analysis
                    except Exception as db_err:
                        await self.db.rollback()
                        cached = await self.get_cached_analysis(video_id)
                        if cached:
                            logger.info(f"AI Cache Hit (after conflict): Returning saved analysis for video {video_id}")
                            return cached
                        logger.error(f"DB Error saving AI analysis: {db_err}")
                        raise db_err
                else:
                    logger.error(f"LM Studio API returned error status: {response.status_code}")
                    raise RuntimeError(f"LM Studio Error: {response.text}")
                    
        except Exception as e:
            logger.error(f"Failed to communicate with LM Studio API: {e}. Falling back to default mockup.")
            # Fallback to Mockup to prevent API failures from crashing the system
            return await self._build_fallback_analysis(video_id, video, velocity)
