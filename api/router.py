from fastapi import APIRouter
from api.videos import router as videos_router
from api.channels import router as channels_router
from api.ranking import router as ranking_router
from api.compare import router as compare_router
from api.trending import router as trending_router
from api.ai import router as ai_router
from api.alerts import router as alerts_router
from api.prediction import router as prediction_router
from api.admin import router as admin_router

api_router = APIRouter()

# Include all sub-routers
api_router.include_router(videos_router)
api_router.include_router(channels_router)
api_router.include_router(ranking_router)
api_router.include_router(compare_router)
api_router.include_router(trending_router)
api_router.include_router(ai_router)
api_router.include_router(alerts_router)
api_router.include_router(prediction_router)
api_router.include_router(admin_router)


