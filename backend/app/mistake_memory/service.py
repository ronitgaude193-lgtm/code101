"""
Intelligent Mistake Memory: storage, Déjà Vu detection and Memory Replay.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import psycopg

from app.ai_mentor.service import ai_mentor_service
from app.mistake_memory.classifier import Mistake


def _snippet(code: str, max_lines: int = 30, max_chars: int = 1500) -> str:
    lines = (code or "").splitlines()[:max_lines]
    return "\n".join(lines)[:max_chars]


def _ago(ts: Optional[datetime]) -> str:
    if not ts:
        return "earlier"
    delta = datetime.now(timezone.utc) - ts
    if delta.days >= 2:
        return f"{delta.days} days ago"
    if delta.days == 1:
        return "yesterday"
    hours = delta.seconds // 3600
    if hours >= 1:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    minutes = max(1, delta.seconds // 60)
    return f"{minutes} minute{'s' if minutes != 1 else ''} ago"


def _occurrence_view(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "occurrence_id": row["id"],
        "context_type": row["context_type"],
        "context_id": row["context_id"],
        "context_title": row["context_title"],
        "code_snippet": row["code_snippet"],
        "error_excerpt": row["error_excerpt"],
        "explanation": row["explanation"],
        "suggested_correction": row["suggested_correction"],
        "fixed_code_snippet": row["fixed_code_snippet"],
        "resolved": row["resolved_at"] is not None,
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "when": _ago(row["created_at"]),
    }


class MistakeMemoryService:
    # ------------------------------------------------------------------ write
    def record(
        self,
        conn: psycopg.Connection,
        user_id: str,
        mistake: Mistake,
        context_type: str,
        context_id: Optional[str],
        context_title: Optional[str],
        code: str,
        error_excerpt: Optional[str],
    ) -> Dict[str, Any]:
        """Stores the mistake and returns the Déjà Vu analysis (computed before storing)."""
        cur = conn.cursor()
        deja_vu = self._deja_vu(cur, user_id, mistake)

        cur.execute("""
        INSERT INTO mistake_patterns (id, user_id, signature, category, concept, language, occurrences,
                                      last_explanation, last_correction)
        VALUES (%s, %s, %s, %s, %s, %s, 1, %s, %s)
        ON CONFLICT (user_id, signature) DO UPDATE SET
            occurrences = mistake_patterns.occurrences + 1,
            last_seen = now(),
            last_explanation = EXCLUDED.last_explanation,
            last_correction = EXCLUDED.last_correction
        RETURNING id, occurrences;
        """, (str(uuid.uuid4()), user_id, mistake.signature, mistake.category, mistake.concept, mistake.language,
              mistake.explanation, mistake.correction))
        pattern = cur.fetchone()

        occurrence_id = str(uuid.uuid4())
        cur.execute("""
        INSERT INTO mistake_occurrences (id, pattern_id, user_id, context_type, context_id, context_title,
                                         code_snippet, error_excerpt, explanation, suggested_correction)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (occurrence_id, pattern["id"], user_id, context_type, context_id, context_title, _snippet(code),
              (error_excerpt or "")[:800] or None, mistake.explanation, mistake.correction))

        deja_vu["occurrence_id"] = occurrence_id
        deja_vu["pattern_id"] = pattern["id"]
        deja_vu["occurrences"] = pattern["occurrences"]
        return deja_vu

    def resolve_context(self, conn: psycopg.Connection, user_id: str, context_type: str, context_id: str, code: str) -> int:
        """When a student passes a task they previously failed, remember how they fixed it."""
        cur = conn.cursor()
        cur.execute("""
        UPDATE mistake_occurrences
        SET resolved_at = now(), fixed_code_snippet = %s
        WHERE user_id = %s AND context_type = %s AND context_id = %s AND resolved_at IS NULL
        RETURNING pattern_id;
        """, (_snippet(code), user_id, context_type, context_id))
        pattern_ids = {r["pattern_id"] for r in cur.fetchall()}
        for pid in pattern_ids:
            cur.execute("UPDATE mistake_patterns SET resolved_count = resolved_count + 1 WHERE id = %s;", (pid,))
        return len(pattern_ids)

    # ------------------------------------------------------------- Déjà Vu
    def _deja_vu(self, cur, user_id: str, mistake: Mistake) -> Dict[str, Any]:
        current = {
            "category": mistake.category,
            "concept": mistake.concept,
            "signature": mistake.signature,
            "explanation": mistake.explanation,
            "suggested_correction": mistake.correction,
        }
        # 1. Same signature = genuinely repeated mistake
        cur.execute("""
        SELECT o.*, p.category, p.concept, p.occurrences
        FROM mistake_occurrences o JOIN mistake_patterns p ON p.id = o.pattern_id
        WHERE o.user_id = %s AND p.signature = %s
        ORDER BY (o.resolved_at IS NOT NULL) DESC, o.created_at DESC
        LIMIT 1;
        """, (user_id, mistake.signature))
        prev = cur.fetchone()
        if prev:
            times = prev["occurrences"] + 1
            how_fixed = (" Last time you fixed it - compare your current code with the version that passed."
                         if prev["resolved_at"] else "")
            return {
                "status": "repeat",
                "current": current,
                "previous": dict(_occurrence_view(prev), category=prev["category"], concept=prev["concept"]),
                "related_concept": mistake.concept,
                "recommendation": (f"This is the {self._ordinal(times)} time this exact mistake has appeared "
                                   f"({mistake.category}). {mistake.correction}{how_fixed}"),
            }

        # 2. Same concept, different mistake = related (not a repeat)
        cur.execute("""
        SELECT o.*, p.category, p.concept, p.occurrences
        FROM mistake_occurrences o JOIN mistake_patterns p ON p.id = o.pattern_id
        WHERE o.user_id = %s AND p.concept = %s AND p.signature <> %s
        ORDER BY o.created_at DESC
        LIMIT 1;
        """, (user_id, mistake.concept, mistake.signature))
        rel = cur.fetchone()
        if rel:
            return {
                "status": "related",
                "current": current,
                "previous": dict(_occurrence_view(rel), category=rel["category"], concept=rel["concept"]),
                "related_concept": mistake.concept,
                "recommendation": (f"A different mistake in the same concept ({mistake.concept}) happened before: "
                                   f"{rel['category']}. Review the {mistake.concept} lesson notes. {mistake.correction}"),
            }

        return {
            "status": "first_time",
            "current": current,
            "previous": None,
            "related_concept": mistake.concept,
            "recommendation": mistake.correction,
        }

    @staticmethod
    def _ordinal(n: int) -> str:
        suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"

    # ------------------------------------------------------------------ read
    def list_patterns(self, conn: psycopg.Connection, user_id: str) -> List[Dict[str, Any]]:
        cur = conn.cursor()
        cur.execute("""
        SELECT * FROM mistake_patterns WHERE user_id = %s ORDER BY occurrences DESC, last_seen DESC;
        """, (user_id,))
        patterns = cur.fetchall()
        result = []
        for p in patterns:
            cur.execute("""
            SELECT * FROM mistake_occurrences WHERE pattern_id = %s ORDER BY created_at DESC LIMIT 5;
            """, (p["id"],))
            occ = [_occurrence_view(r) for r in cur.fetchall()]
            result.append({
                "pattern_id": p["id"],
                "signature": p["signature"],
                "category": p["category"],
                "concept": p["concept"],
                "language": p["language"],
                "occurrences": p["occurrences"],
                "resolved_count": p["resolved_count"],
                "is_repeated": p["occurrences"] >= 2,
                "explanation": p["last_explanation"],
                "suggested_correction": p["last_correction"],
                "first_seen": p["first_seen"].isoformat() if p["first_seen"] else None,
                "last_seen": p["last_seen"].isoformat() if p["last_seen"] else None,
                "recent_occurrences": occ,
            })
        return result

    def get_occurrence(self, conn: psycopg.Connection, user_id: str, occurrence_id: str) -> Optional[Dict[str, Any]]:
        cur = conn.cursor()
        cur.execute("""
        SELECT o.*, p.signature, p.category, p.concept, p.language
        FROM mistake_occurrences o JOIN mistake_patterns p ON p.id = o.pattern_id
        WHERE o.id = %s AND o.user_id = %s;
        """, (occurrence_id, user_id))
        return cur.fetchone()

    def relevant_history(self, conn: psycopg.Connection, user_id: str, signature: str, concept: str,
                         exclude_occurrence_id: Optional[str], limit: int = 3) -> List[Dict[str, Any]]:
        """Only the most relevant few occurrences - never the student's whole history."""
        cur = conn.cursor()
        cur.execute("""
        SELECT o.*, p.signature, p.category, p.concept,
               CASE WHEN p.signature = %s THEN 'repeat' ELSE 'related' END AS relation
        FROM mistake_occurrences o JOIN mistake_patterns p ON p.id = o.pattern_id
        WHERE o.user_id = %s AND (p.signature = %s OR p.concept = %s) AND o.id <> %s
        ORDER BY (p.signature = %s) DESC, (o.resolved_at IS NOT NULL) DESC, o.created_at DESC
        LIMIT %s;
        """, (signature, user_id, signature, concept, exclude_occurrence_id or "", signature, limit))
        return cur.fetchall()

    # -------------------------------------------------------- Memory Replay
    async def replay(self, conn: psycopg.Connection, user_id: str, occurrence_id: str) -> Optional[Dict[str, Any]]:
        occ = self.get_occurrence(conn, user_id, occurrence_id)
        if not occ:
            return None
        history = self.relevant_history(conn, user_id, occ["signature"], occ["concept"], occurrence_id)

        current = {
            "occurrence_id": occ["id"],
            "category": occ["category"],
            "concept": occ["concept"],
            "language": occ["language"],
            "context_title": occ["context_title"],
            "code_snippet": occ["code_snippet"],
            "error_excerpt": occ["error_excerpt"],
        }
        generic = await self._generic_feedback(occ)
        references = [
            {
                "relation": h["relation"],
                "category": h["category"],
                "context_title": h["context_title"],
                "when": _ago(h["created_at"]),
                "resolved": h["resolved_at"] is not None,
                "suggested_correction": h["suggested_correction"],
                "fixed_code_snippet": h["fixed_code_snippet"],
            }
            for h in history
        ]

        if not history:
            return {
                "current_mistake": current,
                "generic": generic,
                "personalized": None,
                "first_time": True,
                "first_time_message": ("This is the first time Mistake Memory has seen this kind of mistake from you, "
                                       "so there is no history to personalise with yet. The generic feedback applies. "
                                       "If it happens again, Memory Replay will connect the two."),
                "memory_used": [],
            }

        personalized = await self._personalized_feedback(occ, history) or self._personalized_fallback(occ, history)
        return {
            "current_mistake": current,
            "generic": generic,
            "personalized": personalized,
            "first_time": False,
            "first_time_message": None,
            "memory_used": references,
        }

    async def _generic_feedback(self, occ: Dict[str, Any]) -> Dict[str, Any]:
        """Feedback from the current submission alone (no history) - the existing AI Mentor."""
        mentor = await ai_mentor_service.get_mentor_response(
            code=occ["code_snippet"] or "",
            mode="debugging",
            language=occ["language"],
            challenge_title=occ["context_title"],
            error_message=occ["error_excerpt"],
        )
        if mentor.is_simulated and occ["language"] != "python":
            # The offline rule engine is Python-specific; use the classifier's explanation instead.
            return {
                "summary": occ["category"],
                "explanation": occ["explanation"] or "",
                "hints": [occ["suggested_correction"]] if occ["suggested_correction"] else [],
                "source": "rules",
            }
        return {
            "summary": mentor.summary,
            "explanation": mentor.explanation,
            "hints": mentor.hints[:3],
            "source": "rules" if mentor.is_simulated else "llm",
        }

    async def _personalized_feedback(self, occ: Dict[str, Any], history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        memory_lines = []
        for i, h in enumerate(history, start=1):
            fixed = "yes - the student later fixed it" if h["resolved_at"] else "not yet fixed"
            memory_lines.append(
                f"{i}. [{h['relation']}] {h['category']} in '{h['context_title']}' ({_ago(h['created_at'])}); "
                f"correction suggested: {h['suggested_correction']}; {fixed}."
            )
        system = (
            "You are a programming tutor giving PERSONALISED feedback using the student's own mistake history. "
            "Use only the history provided; never invent past events, scores or completions. "
            "Do not give the full solution. Reply with JSON: "
            '{"summary": "one sentence", "explanation": "2-4 sentences connecting the current mistake to the past ones", '
            '"what_to_do_differently": "one concrete action for this attempt"}'
        )
        user = (
            f"Language: {occ['language']}\nTask: {occ['context_title']}\n"
            f"Current mistake: {occ['category']} (concept: {occ['concept']})\n"
            f"Error/evidence: {occ['error_excerpt'] or 'wrong output'}\n"
            f"Current code (excerpt):\n{(occ['code_snippet'] or '')[:800]}\n\n"
            f"Relevant past mistakes:\n" + "\n".join(memory_lines)
        )
        data = await ai_mentor_service.generate_json(system, user, ["summary", "explanation", "what_to_do_differently"])
        if not data:
            return None
        return {
            "summary": str(data["summary"])[:300],
            "explanation": str(data["explanation"])[:1200],
            "what_to_do_differently": str(data["what_to_do_differently"])[:400],
            "source": "llm",
        }

    def _personalized_fallback(self, occ: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
        top = history[0]
        if top["relation"] == "repeat":
            summary = f"You have made this {occ['category'].lower()} mistake before."
            explanation = (f"{_ago(top['created_at']).capitalize()}, in '{top['context_title']}', the same pattern appeared. "
                           f"The correction then was: {top['suggested_correction']}")
            if top["resolved_at"]:
                explanation += " You fixed it that time, so you already know the fix - look at how your passing version differed."
        else:
            summary = f"This is a new mistake, but in a concept you have struggled with before: {occ['concept']}."
            explanation = (f"Previously ({_ago(top['created_at'])}, '{top['context_title']}') you had a "
                           f"{top['category'].lower()} issue. Both mistakes come from the same idea, {occ['concept']}.")
        return {
            "summary": summary,
            "explanation": explanation,
            "what_to_do_differently": f"Before you submit again: {occ['suggested_correction']}",
            "source": "rules",
        }


mistake_memory_service = MistakeMemoryService()
