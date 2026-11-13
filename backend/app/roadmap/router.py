from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user_payload
from app.database.session import get_db
from app.roadmap.service import roadmap_service
from app.schemas.all_schemas import RoadmapGenerateRequest

router = APIRouter(prefix="/api/roadmap", tags=["Personalized Roadmap"])


@router.get("")
def get_roadmap(user_payload: dict = Depends(get_current_user_payload)):
    """Returns the active roadmap (or null). Verified progress is synced on every read."""
    with get_db() as conn:
        return {"roadmap": roadmap_service.get_active(conn, user_payload["sub"])}


@router.post("/generate")
async def generate_roadmap(req: RoadmapGenerateRequest, user_payload: dict = Depends(get_current_user_payload)):
    with get_db() as conn:
        return {"roadmap": await roadmap_service.generate(conn, user_payload["sub"], req.track)}


@router.post("/days/{day_id}/complete")
def complete_day(day_id: str, user_payload: dict = Depends(get_current_user_payload)):
    with get_db() as conn:
        res = roadmap_service.complete_day(conn, user_payload["sub"], day_id)
        if res.get("status_code") == 404:
            raise HTTPException(status_code=404, detail=res["message"])
        return res
