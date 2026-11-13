"""
Learning-strain detection and progressive hint generation.

"Learning strain" is a transparent, rule-based score (0-100) computed from recorded
activity - consecutive failures, repeated mistakes, hint requests, declining accuracy,
long sessions and lack of progress. It describes *difficulty with a task*; it is not a
medical or psychological assessment. The LLM only words the hints; it never decides
the score, never decides when to intervene and never sees a full solution.
"""
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import psycopg

from app.ai_mentor.service import ai_mentor_service
from app.adaptive_learning.engine import adaptive_engine

OFFER_THRESHOLD = 45          # offer a hint at or above this score
HIGH_THRESHOLD = 70           # recovery recommendations at or above this score
SESSION_GAP = timedelta(minutes=30)
DISMISS_COOLDOWN_FAILURES = 2 # after "no thanks", wait for 2 more failures before offering again
MAX_HINT_LEVEL = 3

HINT_LEVEL_NAMES = {1: "Conceptual hint", 2: "Directional hint", 3: "Guided hint"}
HINT_LEVEL_INSTRUCTIONS = {
    1: "Level 1 - CONCEPTUAL: name the concept the student should reconsider and why it matters here. No code, no specific fix.",
    2: "Level 2 - DIRECTIONAL: point to the part of their approach (which line/construct) that needs to change and in what direction, without writing the fix.",
    3: "Level 3 - GUIDED: explain the key logic or steps of a correct approach in plain words. You may show at most ONE short line of code. Never the full solution.",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AssistanceService:
    # --------------------------------------------------------- context info
    def get_context(self, conn: psycopg.Connection, context_type: str, context_id: str) -> Optional[Dict[str, Any]]:
        cur = conn.cursor()
        if context_type == "challenge":
            cur.execute("SELECT id, title, description AS prompt, topic AS concept, difficulty, hints FROM coding_challenges WHERE id = %s;", (context_id,))
            row = cur.fetchone()
            if row:
                return dict(row, language="python", kind="practice", lesson_id=None, lesson_title=None, level_id=None, course_id=None)
        elif context_type == "course_task":
            cur.execute("""
            SELECT t.id, t.title, t.prompt, t.concept, t.difficulty, t.hints, t.task_type, t.kind, t.level_id, t.lesson_id,
                   l.title AS lesson_title, c.id AS course_id, c.language
            FROM course_tasks t
            JOIN course_levels lv ON lv.id = t.level_id
            JOIN courses c ON c.id = lv.course_id
            LEFT JOIN course_lessons l ON l.id = t.lesson_id
            WHERE t.id = %s;
            """, (context_id,))
            row = cur.fetchone()
            if row:
                language = "quiz" if row["task_type"] == "quiz" else row["language"]
                return dict(row, language=language)
        return None

    # -------------------------------------------------------------- strain
    def compute_strain(self, conn: psycopg.Connection, user_id: str, context_type: str, context_id: str) -> Dict[str, Any]:
        cur = conn.cursor()
        now = _utcnow()

        cur.execute("""
        SELECT passed, mistake_signature, created_at FROM practice_attempts
        WHERE user_id = %s AND context_type = %s AND context_id = %s
        ORDER BY created_at DESC LIMIT 30;
        """, (user_id, context_type, context_id))
        ctx_attempts = cur.fetchall()

        cur.execute("""
        SELECT passed, created_at FROM practice_attempts
        WHERE user_id = %s ORDER BY created_at DESC LIMIT 60;
        """, (user_id,))
        all_attempts = cur.fetchall()

        signals: List[Dict[str, Any]] = []

        def add(name: str, points: int, detail: str):
            if points > 0:
                signals.append({"signal": name, "points": points, "detail": detail})

        # 1. Consecutive failures on this problem (since the last pass)
        consecutive = 0
        for a in ctx_attempts:
            if a["passed"]:
                break
            consecutive += 1
        add("consecutive_failures", min(consecutive * 15, 45),
            f"{consecutive} incorrect submission{'s' if consecutive != 1 else ''} in a row on this problem")

        # 2. Repeated mistake (same signature) within the current streak of failures
        failing = [a["mistake_signature"] for a in ctx_attempts[:consecutive] if a["mistake_signature"]]
        repeats = len(failing) - len(set(failing))
        add("repeated_mistake", min(repeats * 10, 20),
            f"the same mistake repeated {repeats} time{'s' if repeats != 1 else ''} while working on this problem")

        # 3. Hint requests on this problem in the last 30 minutes
        cur.execute("""
        SELECT COUNT(*) AS n FROM hint_history
        WHERE user_id = %s AND context_type = %s AND context_id = %s AND created_at > %s;
        """, (user_id, context_type, context_id, now - timedelta(minutes=30)))
        hints_recent = cur.fetchone()["n"]
        add("frequent_hints", min(hints_recent * 5, 15), f"{hints_recent} hint{'s' if hints_recent != 1 else ''} requested in the last 30 minutes")

        # 4. Many attempts at the same problem today
        today_attempts = sum(1 for a in ctx_attempts if a["created_at"] > now - timedelta(hours=24))
        if today_attempts >= 5:
            add("many_attempts", 10, f"{today_attempts} attempts at this problem in the last 24 hours")

        # 5. Declining recent accuracy (last 5 vs previous 5 graded attempts)
        if len(all_attempts) >= 10:
            recent = sum(1 for a in all_attempts[:5] if a["passed"]) / 5
            before = sum(1 for a in all_attempts[5:10] if a["passed"]) / 5
            if before - recent >= 0.4:
                add("declining_accuracy", 10,
                    f"accuracy dropped from {int(before * 100)}% to {int(recent * 100)}% over the last 10 attempts")

        # 6. Extended session (activity with gaps under 30 minutes)
        session_minutes = 0
        if all_attempts and now - all_attempts[0]["created_at"] < SESSION_GAP:
            start = all_attempts[0]["created_at"]
            for prev, nxt in zip(all_attempts, all_attempts[1:]):
                if prev["created_at"] - nxt["created_at"] > SESSION_GAP:
                    break
                start = nxt["created_at"]
            session_minutes = int((now - start).total_seconds() // 60)
        if session_minutes >= 90:
            add("long_session", 20, f"practising continuously for about {session_minutes} minutes")
        elif session_minutes >= 45:
            add("long_session", 10, f"practising continuously for about {session_minutes} minutes")

        # 7. No progress: 3+ attempts on this problem in 30 minutes without a pass
        window = [a for a in ctx_attempts if a["created_at"] > now - timedelta(minutes=30)]
        if len(window) >= 3 and not any(a["passed"] for a in window):
            add("no_progress", 10, f"{len(window)} attempts in the last 30 minutes without passing")

        score = min(100, sum(s["points"] for s in signals))
        level = "high" if score >= HIGH_THRESHOLD else ("moderate" if score >= 30 else "low")

        hints_used = self._hints_used(cur, user_id, context_type, context_id)
        offer = self._should_offer(cur, user_id, context_type, context_id, score, consecutive, hints_used)

        recovery: List[Dict[str, Any]] = []
        if score >= HIGH_THRESHOLD or (hints_used >= MAX_HINT_LEVEL and consecutive >= 1):
            recovery = self.recovery_suggestions(conn, user_id, context_type, context_id, session_minutes)

        return {
            "context_type": context_type,
            "context_id": context_id,
            "strain_score": score,
            "level": level,
            "signals": signals,
            "consecutive_failures": consecutive,
            "session_minutes": session_minutes,
            "hints_used": hints_used,
            "next_hint_level": min(hints_used + 1, MAX_HINT_LEVEL) if hints_used < MAX_HINT_LEVEL else None,
            "offer_hint": offer,
            "message": ("We noticed you're having difficulty with this problem. Would you like a small hint?"
                        if offer else None),
            "recovery": recovery,
            "recommended_difficulty": adaptive_engine.get_practice_difficulty(conn, user_id),
            "disclaimer": "Learning strain reflects recent practice activity only. It is not a medical or psychological assessment.",
        }

    def _hints_used(self, cur, user_id, context_type, context_id) -> int:
        cur.execute("""
        SELECT COALESCE(MAX(hint_level), 0) AS lvl FROM hint_history
        WHERE user_id = %s AND context_type = %s AND context_id = %s;
        """, (user_id, context_type, context_id))
        return cur.fetchone()["lvl"]

    def _should_offer(self, cur, user_id, context_type, context_id, score, consecutive, hints_used) -> bool:
        if hints_used >= MAX_HINT_LEVEL or consecutive == 0:
            return False
        if score < OFFER_THRESHOLD and consecutive < 3:
            return False
        cur.execute("""
        SELECT response, created_at FROM assistance_prompts
        WHERE user_id = %s AND context_type = %s AND context_id = %s
        ORDER BY created_at DESC LIMIT 1;
        """, (user_id, context_type, context_id))
        last = cur.fetchone()
        if last and last["response"] == "dismissed":
            cur.execute("""
            SELECT COUNT(*) AS n FROM practice_attempts
            WHERE user_id = %s AND context_type = %s AND context_id = %s AND passed = FALSE AND created_at > %s;
            """, (user_id, context_type, context_id, last["created_at"]))
            if cur.fetchone()["n"] < DISMISS_COOLDOWN_FAILURES:
                return False
        return True

    def record_attempt(self, conn: psycopg.Connection, user_id: str, context_type: str, context_id: str,
                       passed: bool, concept: Optional[str], mistake_signature: Optional[str],
                       execution_seconds: float = 0.0) -> None:
        """Every graded attempt is timestamped here - the raw data for strain scoring."""
        conn.cursor().execute("""
        INSERT INTO practice_attempts (id, user_id, context_type, context_id, passed, concept, mistake_signature, execution_seconds)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (str(uuid.uuid4()), user_id, context_type, context_id, passed, concept, mistake_signature, execution_seconds))

    def record_response(self, conn: psycopg.Connection, user_id: str, context_type: str, context_id: str,
                        accepted: bool, strain_score: int) -> None:
        conn.cursor().execute("""
        INSERT INTO assistance_prompts (id, user_id, context_type, context_id, strain_score, response)
        VALUES (%s, %s, %s, %s, %s, %s);
        """, (str(uuid.uuid4()), user_id, context_type, context_id, strain_score, "accepted" if accepted else "dismissed"))

    # ------------------------------------------------------------ recovery
    def recovery_suggestions(self, conn: psycopg.Connection, user_id: str, context_type: str, context_id: str,
                             session_minutes: int) -> List[Dict[str, Any]]:
        cur = conn.cursor()
        ctx = self.get_context(conn, context_type, context_id) or {}
        out: List[Dict[str, Any]] = []

        if session_minutes >= 45:
            out.append({"type": "break", "title": "Take a short break",
                        "detail": f"You've been practising for about {session_minutes} minutes. A 5-10 minute break often makes the bug obvious when you return.",
                        "target_type": None, "target_id": None})
        else:
            out.append({"type": "break", "title": "Step away for a moment",
                        "detail": "Several attempts in a row haven't passed. A short pause and re-reading the problem statement can help.",
                        "target_type": None, "target_id": None})

        if ctx.get("lesson_id"):
            out.append({"type": "review", "title": f"Review the lesson: {ctx['lesson_title']}",
                        "detail": f"Re-read the explanation and examples for {ctx.get('concept')}.",
                        "target_type": "course_lesson", "target_id": ctx["lesson_id"]})
        elif ctx.get("concept"):
            out.append({"type": "review", "title": f"Review the concept: {ctx['concept']}",
                        "detail": "Ask the AI Mentor in Learning mode to explain the concept with a small example.",
                        "target_type": None, "target_id": None})

        easier = None
        if context_type == "course_task" and ctx.get("level_id"):
            cur.execute("""
            SELECT t.id, t.title FROM course_tasks t
            WHERE t.level_id = %s AND t.kind = 'practice' AND t.id <> %s
              AND NOT EXISTS (SELECT 1 FROM course_completions cc
                              WHERE cc.user_id = %s AND cc.item_type = 'task' AND cc.item_id = t.id)
            ORDER BY CASE t.difficulty WHEN 'Beginner' THEN 0 WHEN 'Intermediate' THEN 1 ELSE 2 END, t.sort_order
            LIMIT 1;
            """, (ctx["level_id"], context_id, user_id))
            row = cur.fetchone()
            if row:
                easier = {"target_type": "course_task", "target_id": row["id"], "title": row["title"]}
        if easier is None:
            cur.execute("""
            SELECT c.id, c.title FROM coding_challenges c
            WHERE c.difficulty = 'Beginner' AND c.id <> %s AND (c.visibility = 'public' OR c.created_by = %s)
              AND NOT EXISTS (SELECT 1 FROM code_submissions s
                              WHERE s.user_id = %s AND s.challenge_id = c.id AND s.status = 'Accepted')
            ORDER BY c.xp_reward ASC LIMIT 1;
            """, (context_id, user_id, user_id))
            row = cur.fetchone()
            if row:
                easier = {"target_type": "challenge", "target_id": row["id"], "title": row["title"]}
        if easier:
            out.append({"type": "easier_problem", "title": f"Try an easier problem: {easier['title']}",
                        "detail": "Build confidence on a related, lower-difficulty problem, then come back to this one.",
                        "target_type": easier["target_type"], "target_id": easier["target_id"]})
        return out

    # --------------------------------------------------------------- hints
    async def next_hint(self, conn: psycopg.Connection, user_id: str, context_type: str, context_id: str,
                        code: Optional[str]) -> Dict[str, Any]:
        ctx = self.get_context(conn, context_type, context_id)
        if not ctx:
            raise ValueError("Unknown problem")
        if ctx.get("kind") in ("assessment", "final"):
            raise ValueError("Hints are not available during assessments. Review the level's lessons instead.")
        cur = conn.cursor()
        used = self._hints_used(cur, user_id, context_type, context_id)
        if used >= MAX_HINT_LEVEL:
            strain = self.compute_strain(conn, user_id, context_type, context_id)
            return {"level": None, "level_name": None, "hint": None, "source": None, "exhausted": True,
                    "hints_remaining": 0, "recovery": strain["recovery"] or
                    self.recovery_suggestions(conn, user_id, context_type, context_id, strain["session_minutes"])}

        level = used + 1
        strain_score = self.compute_strain(conn, user_id, context_type, context_id)["strain_score"]
        authored = []
        try:
            authored = json.loads(ctx.get("hints") or "[]")
        except (TypeError, ValueError):
            authored = []

        # Most relevant memory item for this problem (keeps the prompt small)
        cur.execute("""
        SELECT p.category, p.last_correction FROM practice_attempts a
        JOIN mistake_patterns p ON p.user_id = a.user_id AND p.signature = a.mistake_signature
        WHERE a.user_id = %s AND a.context_type = %s AND a.context_id = %s AND a.passed = FALSE
        ORDER BY a.created_at DESC LIMIT 1;
        """, (user_id, context_type, context_id))
        recent_mistake = cur.fetchone()

        hint, source = await self._llm_hint(ctx, level, code, recent_mistake, authored)
        if not hint:
            if len(authored) >= level:
                hint, source = authored[level - 1], "authored"
            else:
                hint, source = self._template_hint(ctx, level, recent_mistake), "rules"
            if recent_mistake and level >= 2 and source != "llm":
                hint += f" (Your last attempt showed: {recent_mistake['category']}.)"

        cur.execute("""
        INSERT INTO hint_history (id, user_id, context_type, context_id, hint_level, hint_text, source, strain_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (str(uuid.uuid4()), user_id, context_type, context_id, level, hint, source, strain_score))
        # Also log to ai_feedback so the existing Programming DNA hint-independence score sees it.
        cur.execute("""
        INSERT INTO ai_feedback (id, submission_id, user_id, mode, summary, detailed_explanation, hints_given, misconceptions, suggested_topics)
        VALUES (%s, NULL, %s, 'hint', %s, %s, %s, %s, %s);
        """, (str(uuid.uuid4()), user_id, f"{HINT_LEVEL_NAMES[level]} for {ctx['title']}", hint,
              json.dumps([hint]), json.dumps([recent_mistake["category"]] if recent_mistake else []),
              json.dumps([ctx.get("concept")])))

        return {
            "level": level,
            "level_name": HINT_LEVEL_NAMES[level],
            "hint": hint,
            "source": source,
            "exhausted": False,
            "hints_remaining": MAX_HINT_LEVEL - level,
            "recovery": [],
        }

    async def _llm_hint(self, ctx, level, code, recent_mistake, authored):
        system = (
            "You are a programming tutor giving ONE progressive hint. Never reveal the complete solution, never write "
            "the whole corrected program, and never claim the student passed anything. Encourage independent thinking. "
            f"{HINT_LEVEL_INSTRUCTIONS[level]} Reply with JSON: {{\"hint\": \"the hint, at most 3 sentences\"}}"
        )
        user = (
            f"Problem: {ctx['title']}\nLanguage: {ctx.get('language')}\nConcept: {ctx.get('concept')}\n"
            f"Statement: {(ctx.get('prompt') or '')[:700]}\n"
            f"Student's current code (excerpt):\n{(code or '')[:900]}\n"
            f"Most recent recorded mistake: {recent_mistake['category'] if recent_mistake else 'none recorded'}\n"
            f"Instructor's reference hint for this level (rephrase for this student, do not go further): "
            f"{authored[level - 1] if len(authored) >= level else 'n/a'}"
        )
        data = await ai_mentor_service.generate_json(system, user, ["hint"])
        if not data:
            return None, None
        hint = str(data["hint"]).strip()
        # Safety net: reject hints that smuggle in a solution (multi-line code blocks or very long answers).
        if "```" in hint or len(hint) > 600 or len(re.findall(r"[;{}]\s*$", hint, re.M)) > 2:
            return None, None
        return hint, "llm"

    def _template_hint(self, ctx, level, recent_mistake) -> str:
        concept = ctx.get("concept") or "the core idea"
        if level == 1:
            return f"Focus on {concept}. Re-read the problem statement and write down, in plain words, what the program must do with the first example."
        if level == 2:
            fix = recent_mistake["last_correction"] if recent_mistake and recent_mistake.get("last_correction") else \
                "Compare your output with the expected output line by line and find the first place they differ."
            return f"Look closely at the part of your code that handles {concept}. {fix}"
        return (f"Break the solution into steps: read the input, apply the {concept} logic one step at a time, then print exactly "
                f"the required format. Check each step with the first example input before submitting.")


assistance_service = AssistanceService()
