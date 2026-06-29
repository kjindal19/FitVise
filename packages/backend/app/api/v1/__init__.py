"""Aggregates all v1 REST routers under /api/v1."""
from fastapi import APIRouter

from app.api.v1 import (
    auth,
    checkins,
    diet,
    export,
    health,
    journal,
    metrics,
    notifications,
    profile,
    programme,
    recovery,
    workouts,
)

api_router = APIRouter(prefix="/api/v1")

# health is mounted at /api/v1/health AND at the bare /health (see main.py)
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(programme.router)
api_router.include_router(workouts.router)
api_router.include_router(diet.router)
api_router.include_router(metrics.router)
api_router.include_router(recovery.router)
api_router.include_router(journal.router)
api_router.include_router(checkins.router)
api_router.include_router(notifications.router)
api_router.include_router(export.router)
