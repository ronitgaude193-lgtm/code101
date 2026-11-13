import uuid
import json
from typing import Optional
from fastapi import APIRouter, Depends
from app.database.session import get_db
from app.core.security import get_optional_user_payload
from app.ai_mentor.service import ai_mentor_service
from app.schemas.all_schemas import (
    AIMentorRequest,
    AIMentorResponse,
    AutopsyRequest,
    AutopsyResponse
)

router = APIRouter(prefix="/api/ai", tags=["AI Mentor & Autopsy"])

@router.post("/mentor", response_model=AIMentorResponse)
async def ask_mentor(req: AIMentorRequest, user_payload: Optional[dict] = Depends(get_optional_user_payload)):
    challenge_title = None
    if req.challenge_id:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title FROM coding_challenges WHERE id = %s;", (req.challenge_id,))
            row = cursor.fetchone()
            if row:
                challenge_title = row["title"]

    resp = await ai_mentor_service.get_mentor_response(
        code=req.code,
        mode=req.mode,
        language=req.language,
        prompt=req.prompt,
        challenge_title=challenge_title,
        execution_output=req.execution_output,
        error_message=req.error_message
    )

    # Record feedback if user is logged in
    if user_payload and "sub" in user_payload:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO ai_feedback (id, submission_id, user_id, mode, summary, detailed_explanation, hints_given, misconceptions, suggested_topics)
            VALUES (%s, NULL, %s, %s, %s, %s, %s, %s, %s);
            """, (
                str(uuid.uuid4()),
                user_payload["sub"],
                req.mode,
                resp.summary,
                resp.explanation,
                json.dumps(resp.hints),
                json.dumps([resp.conceptual_takeaway]),
                json.dumps(resp.related_topics)
            ))

    return resp

@router.post("/autopsy", response_model=AutopsyResponse)
async def analyze_autopsy(req: AutopsyRequest, user_payload: Optional[dict] = Depends(get_optional_user_payload)):
    challenge_title = None
    if req.challenge_id:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title FROM coding_challenges WHERE id = %s;", (req.challenge_id,))
            row = cursor.fetchone()
            if row:
                challenge_title = row["title"]

    resp = await ai_mentor_service.run_code_autopsy(
        code=req.code,
        language=req.language,
        challenge_title=challenge_title,
        expected_behavior=req.expected_behavior,
        actual_output=req.actual_output,
        error_message=req.error_message
    )

    if user_payload and "sub" in user_payload:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO ai_feedback (id, submission_id, user_id, mode, summary, detailed_explanation, hints_given, misconceptions, suggested_topics)
            VALUES (%s, NULL, %s, 'autopsy', %s, %s, %s, %s, %s);
            """, (
                str(uuid.uuid4()),
                user_payload["sub"],
                resp.primary_failure_reason,
                resp.detailed_walkthrough,
                json.dumps([resp.guiding_hint]),
                json.dumps([resp.misconception_identified]),
                json.dumps([resp.practice_prompt])
            ))

    return resp
