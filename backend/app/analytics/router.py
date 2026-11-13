from fastapi import APIRouter, Depends, HTTPException
from app.database.session import get_db
from app.core.security import get_current_user_payload
from app.adaptive_learning.engine import adaptive_engine
from app.schemas.all_schemas import DashboardResponse, ProgrammingDNAResponse

router = APIRouter(prefix="/api/analytics", tags=["Analytics & Programming DNA"])

@router.get("/dashboard", response_model=DashboardResponse)
def get_student_dashboard(user_payload: dict = Depends(get_current_user_payload)):
    user_id = user_payload["sub"]
    with get_db() as conn:
        try:
            return adaptive_engine.get_dashboard_data(conn, user_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

@router.get("/dna", response_model=ProgrammingDNAResponse)
def get_programming_dna(user_payload: dict = Depends(get_current_user_payload)):
    user_id = user_payload["sub"]
    with get_db() as conn:
        try:
            dash = adaptive_engine.get_dashboard_data(conn, user_id)
            return dash.programming_dna
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
