from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.academy import grading
from app.academy.service import academy_service, AcademyError
from app.core.security import get_current_user_payload, get_optional_user_payload
from app.database.session import get_db
from app.schemas.all_schemas import CourseTaskRunRequest, CourseTaskSubmitRequest

router = APIRouter(prefix="/api/academy", tags=["Coding Academy"])


def _uid(payload: Optional[dict]) -> Optional[str]:
    return payload.get("sub") if payload else None


def _raise(e: AcademyError):
    raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/courses")
def list_courses(user_payload: Optional[dict] = Depends(get_optional_user_payload)):
    with get_db() as conn:
        return academy_service.list_courses(conn, _uid(user_payload))


@router.get("/courses/{slug}")
def get_course(slug: str, user_payload: Optional[dict] = Depends(get_optional_user_payload)):
    with get_db() as conn:
        try:
            return academy_service.course_detail(conn, slug, _uid(user_payload))
        except AcademyError as e:
            _raise(e)


@router.get("/lessons/{lesson_id}")
def get_lesson(lesson_id: str, user_payload: Optional[dict] = Depends(get_optional_user_payload)):
    with get_db() as conn:
        try:
            return academy_service.lesson_detail(conn, lesson_id, _uid(user_payload))
        except AcademyError as e:
            _raise(e)


@router.post("/lessons/{lesson_id}/complete")
def complete_lesson(lesson_id: str, user_payload: dict = Depends(get_current_user_payload)):
    with get_db() as conn:
        try:
            return academy_service.complete_lesson(conn, lesson_id, user_payload["sub"])
        except AcademyError as e:
            _raise(e)


@router.get("/tasks/{task_id}")
def get_task(task_id: str, user_payload: Optional[dict] = Depends(get_optional_user_payload)):
    with get_db() as conn:
        try:
            return academy_service.task_detail(conn, task_id, _uid(user_payload))
        except AcademyError as e:
            _raise(e)


@router.post("/tasks/{task_id}/run")
async def run_task(task_id: str, req: CourseTaskRunRequest,
                   user_payload: Optional[dict] = Depends(get_optional_user_payload)):
    """Runs code / SQL without grading (no XP, no attempt recorded)."""
    with get_db() as conn:
        try:
            sql_result = academy_service.run_task(conn, task_id, _uid(user_payload), req.code, req.stdin or "")
        except AcademyError as e:
            _raise(e)
    if sql_result is not None:
        return sql_result
    res = await grading.run_c_program(req.code, req.stdin or "")
    return {"kind": "code", **res}


@router.post("/tasks/{task_id}/submit")
async def submit_task(task_id: str, req: CourseTaskSubmitRequest,
                      user_payload: dict = Depends(get_current_user_payload)):
    with get_db() as conn:
        try:
            return await academy_service.submit_task(conn, task_id, user_payload["sub"], req.code, req.answers)
        except AcademyError as e:
            _raise(e)
