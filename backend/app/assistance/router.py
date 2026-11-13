from fastapi import APIRouter, Depends, HTTPException, Query

from app.assistance.service import assistance_service
from app.core.security import get_current_user_payload
from app.database.session import get_db
from app.schemas.all_schemas import AssistResponseRequest, HintRequest

router = APIRouter(prefix="/api/assist", tags=["Learning-Strain Assistance"])


@router.get("/strain")
def get_strain(
    context_type: str = Query(..., pattern="^(challenge|course_task)$"),
    context_id: str = Query(..., min_length=1, max_length=100),
    user_payload: dict = Depends(get_current_user_payload),
):
    with get_db() as conn:
        return assistance_service.compute_strain(conn, user_payload["sub"], context_type, context_id)


@router.post("/respond")
def respond_to_offer(req: AssistResponseRequest, user_payload: dict = Depends(get_current_user_payload)):
    """Records whether the student accepted or dismissed a hint offer (dismissals pause further offers)."""
    with get_db() as conn:
        strain = assistance_service.compute_strain(conn, user_payload["sub"], req.context_type, req.context_id)
        assistance_service.record_response(conn, user_payload["sub"], req.context_type, req.context_id,
                                           req.accepted, strain["strain_score"])
        return {"recorded": True, "accepted": req.accepted}


@router.post("/hint")
async def get_next_hint(req: HintRequest, user_payload: dict = Depends(get_current_user_payload)):
    with get_db() as conn:
        try:
            return await assistance_service.next_hint(conn, user_payload["sub"], req.context_type, req.context_id, req.code)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
