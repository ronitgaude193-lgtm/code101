from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user_payload
from app.database.session import get_db
from app.mistake_memory.service import mistake_memory_service
from app.schemas.all_schemas import MemoryReplayRequest

router = APIRouter(prefix="/api/memory", tags=["Mistake Memory & Memory Replay"])


@router.get("/patterns")
def list_patterns(user_payload: dict = Depends(get_current_user_payload)):
    with get_db() as conn:
        patterns = mistake_memory_service.list_patterns(conn, user_payload["sub"])
        return {
            "patterns": patterns,
            "total_mistakes": sum(p["occurrences"] for p in patterns),
            "repeated_patterns": sum(1 for p in patterns if p["is_repeated"]),
        }


@router.post("/replay")
async def memory_replay(req: MemoryReplayRequest, user_payload: dict = Depends(get_current_user_payload)):
    """Generic feedback (current code only) vs personalised feedback (current code + relevant mistake history)."""
    with get_db() as conn:
        res = await mistake_memory_service.replay(conn, user_payload["sub"], req.occurrence_id)
        if res is None:
            raise HTTPException(status_code=404, detail="Mistake not found")
        return res
