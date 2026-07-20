"""
Health-check route.
Kept deliberately dumb right now — it will grow to check DB/Redis connectivity
once those are wired up, which matters a lot at scale for load balancer health checks.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check():
    return {"status": "ok", "service": "clipmind-api"}
