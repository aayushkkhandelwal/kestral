from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.cameras import router as cameras_router
from app.api.v1.videos import router as videos_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.cases import router as cases_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.events import router as events_router
from app.api.v1.zones import router as zones_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(cameras_router)
api_router.include_router(videos_router)
api_router.include_router(evidence_router)
api_router.include_router(cases_router)
api_router.include_router(alerts_router)
api_router.include_router(dashboard_router)
api_router.include_router(events_router)
api_router.include_router(zones_router)
