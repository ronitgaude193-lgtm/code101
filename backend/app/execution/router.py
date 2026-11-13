import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from app.database.session import get_db
from app.core.security import get_optional_user_payload, get_current_user_payload
from app.execution.service import execution_service
from app.execution.visual_tracer import trace_execution
from app.adaptive_learning.engine import adaptive_engine
from app.ai_mentor.service import ai_mentor_service
from app.assistance.service import assistance_service
from app.mistake_memory.classifier import classify_python
from app.mistake_memory.service import mistake_memory_service
from app.schemas.all_schemas import (
    CodeRunRequest,
    CodeRunResponse,
    CodeSubmitRequest,
    CodeSubmitResponse,
    VisualTraceRequest,
    VisualTraceResponse,
    TraceStep
)

router = APIRouter(prefix="/api/execution", tags=["Code Execution"])

@router.post("/run", response_model=CodeRunResponse)
async def run_code(req: CodeRunRequest):
    """
    Executes student code safely via Judge0 (or isolated fallback sandbox).
    """
    res = await execution_service.run_code(req.code, req.language, req.stdin or "")
    return CodeRunResponse(
        stdout=res.get("stdout") or "",
        stderr=res.get("stderr") or "",
        compile_output=res.get("compile_output"),
        exit_code=res.get("exit_code", 0),
        execution_time=res.get("execution_time", 0.0),
        status=res.get("status", "Unknown")
    )

@router.post("/submit", response_model=CodeSubmitResponse)
async def submit_challenge_code(
    req: CodeSubmitRequest,
    user_payload: dict = Depends(get_current_user_payload)
):
    """
    Evaluates challenge code against test cases, stores submission, and updates adaptive learning engine.
    """
    user_id = user_payload["sub"]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, topic, test_cases, xp_reward FROM coding_challenges WHERE id = %s AND (visibility = 'public' OR created_by = %s);", (req.challenge_id, user_id))
        ch_row = cursor.fetchone()
        if not ch_row:
            raise HTTPException(status_code=404, detail="Challenge not found")

        eval_result = await execution_service.evaluate_challenge(
            challenge_id=req.challenge_id,
            student_code=req.code,
            test_cases_json=ch_row["test_cases"],
            language=req.language
        )

        submission_id = str(uuid.uuid4())
        status = eval_result["status"]
        all_passed = eval_result["all_passed"]
        exec_seconds = eval_result.get("execution_time", 0.0)

        # Store in code_submissions
        cursor.execute("""
        INSERT INTO code_submissions (id, user_id, challenge_id, code, language, status, execution_time, error_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            submission_id,
            user_id,
            req.challenge_id,
            req.code,
            req.language,
            status,
            exec_seconds,
            None if all_passed else status
        ))

        # Store execution result
        cursor.execute("""
        INSERT INTO execution_results (id, submission_id, stdout, stderr, exit_code, status_description)
        VALUES (%s, %s, %s, %s, %s, %s);
        """, (
            str(uuid.uuid4()),
            submission_id,
            f"Passed {eval_result['passed_count']}/{eval_result['total_count']} test cases",
            "" if all_passed else "One or more test cases failed.",
            0 if all_passed else 1,
            status
        ))

        # Update Adaptive Learning Engine
        adapt_res = adaptive_engine.record_submission_event(
            conn=conn,
            user_id=user_id,
            challenge_id=req.challenge_id,
            status=status,
            execution_time=exec_seconds,
            error_type=None if all_passed else status
        )

        # Mistake Memory (reuses the AI Code Autopsy rule engine to classify the mistake)
        deja_vu = None
        signature = None
        if not all_passed:
            first_fail = next((t for t in eval_result["test_results"] if not t.passed), None)
            autopsy = ai_mentor_service._generate_rule_based_autopsy(
                req.code,
                first_fail.expected_output if first_fail else None,
                first_fail.actual_output if first_fail else None,
                eval_result.get("first_error"),
            )
            mistake = classify_python(req.code, eval_result.get("first_error"),
                                      autopsy.misconception_identified, ch_row["topic"])
            signature = mistake.signature
            deja_vu = mistake_memory_service.record(
                conn, user_id, mistake, "challenge", req.challenge_id, ch_row["title"], req.code,
                eval_result.get("first_error") or (
                    f"Expected {first_fail.expected_output}, got {first_fail.actual_output}" if first_fail else None),
            )
        else:
            mistake_memory_service.resolve_context(conn, user_id, "challenge", req.challenge_id, req.code)

        # Timestamped attempt -> learning-strain scoring, then roadmap progress
        assistance_service.record_attempt(conn, user_id, "challenge", req.challenge_id, all_passed,
                                          ch_row["topic"], signature, exec_seconds)
        assistance = None if all_passed else assistance_service.compute_strain(
            conn, user_id, "challenge", req.challenge_id)
        from app.roadmap.service import roadmap_service
        roadmap_service.sync_progress(conn, user_id)

        return CodeSubmitResponse(
            submission_id=submission_id,
            status=status,
            all_passed=all_passed,
            passed_count=eval_result["passed_count"],
            total_count=eval_result["total_count"],
            test_results=eval_result["test_results"],
            xp_earned=adapt_res["xp_earned"],
            new_total_xp=adapt_res["new_total_xp"],
            new_level=adapt_res["new_level"],
            new_streak=adapt_res["new_streak"],
            unlocked_achievements=adapt_res["unlocked_achievements"],
            execution_seconds=exec_seconds,
            deja_vu=deja_vu,
            assistance=assistance
        )

@router.post("/trace", response_model=VisualTraceResponse)
def trace_code_execution(req: VisualTraceRequest):
    """
    MODULE G - Visual Code Execution Engine:
    Step-by-step tracing of variables, loop states, function calls, and line events.
    """
    res = trace_execution(req.code, req.stdin or "", req.max_steps)
    steps = [TraceStep(**s) for s in res.get("steps", [])]

    return VisualTraceResponse(
        success=res.get("success", False),
        steps=steps,
        total_steps=res.get("total_steps", len(steps)),
        error=res.get("error"),
        output=res.get("output", "")
    )
