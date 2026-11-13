"""
30-Day Personalized Learning Roadmap.

Personalisation is computed deterministically from recorded data:
- course progress (completed lessons/tasks are skipped; the plan starts where the student is),
- Mistake Memory (concepts with repeated or unresolved mistakes get review days),
- assessment results stored in learning_assessments (weak concepts get review days),
- weak skills from the adaptive engine (low-mastery challenge topics get practice-challenge days),
- current learning strain (a struggling student starts with consolidation before new material).

Ollama/Gemma only writes the focus summary and short coaching tips. It never sees
or decides completion, XP or scores. Day completion is verified against the
database before any XP is awarded, and each day can award XP only once.
"""
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import psycopg

from app.ai_mentor.service import ai_mentor_service
from app.adaptive_learning.engine import adaptive_engine

ROADMAP_DAYS = 30
TRACK_LANGUAGES = {"c": ["c"], "sql": ["sql"], "mixed": ["c", "sql"]}
DAY_XP = {"lesson": 20, "assessment": 30, "review": 10, "challenge": 20}


class RoadmapService:
    # ---------------------------------------------------------- signals
    def _signals(self, cur, user_id: str) -> Dict[str, Any]:
        cur.execute("""
        SELECT concept, SUM(occurrences) AS occ, SUM(resolved_count) AS resolved,
               STRING_AGG(DISTINCT category, ', ') AS categories
        FROM mistake_patterns WHERE user_id = %s
        GROUP BY concept ORDER BY SUM(occurrences) DESC;
        """, (user_id,))
        mistake_concepts = [dict(r) for r in cur.fetchall()]

        cur.execute("""
        SELECT weaknesses FROM learning_assessments
        WHERE user_id = %s AND evaluated_at > now() - interval '30 days'
        ORDER BY evaluated_at DESC LIMIT 10;
        """, (user_id,))
        assessment_weak: Dict[str, int] = {}
        for r in cur.fetchall():
            try:
                for c in json.loads(r["weaknesses"] or "[]"):
                    assessment_weak[c] = assessment_weak.get(c, 0) + 1
            except (TypeError, ValueError):
                pass

        cur.execute("""
        SELECT skill_name, mastery_level FROM student_skills
        WHERE user_id = %s AND mastery_level < 50 ORDER BY mastery_level ASC;
        """, (user_id,))
        weak_skills = [dict(r) for r in cur.fetchall()]

        cur.execute("""
        SELECT COUNT(*) AS total, COALESCE(SUM(CASE WHEN passed THEN 1 ELSE 0 END), 0) AS ok
        FROM practice_attempts WHERE user_id = %s AND created_at > now() - interval '14 days';
        """, (user_id,))
        acc = cur.fetchone()
        return {
            "mistake_concepts": mistake_concepts,
            "assessment_weak": assessment_weak,
            "weak_skills": weak_skills,
            "recent_attempts": acc["total"],
            "recent_accuracy": round(100.0 * acc["ok"] / acc["total"], 1) if acc["total"] else None,
        }

    def _priority_concepts(self, signals: Dict[str, Any]) -> List[Dict[str, Any]]:
        scores: Dict[str, Dict[str, Any]] = {}
        for m in signals["mistake_concepts"]:
            unresolved = max(0, (m["occ"] or 0) - (m["resolved"] or 0))
            if (m["occ"] or 0) >= 2 or unresolved >= 1:
                scores[m["concept"]] = {"concept": m["concept"], "score": (m["occ"] or 0) * 2 + unresolved,
                                        "evidence": f"{m['occ']} recorded mistake(s): {m['categories']}"}
        for concept, n in signals["assessment_weak"].items():
            entry = scores.setdefault(concept, {"concept": concept, "score": 0, "evidence": ""})
            entry["score"] += 3 * n
            entry["evidence"] = (entry["evidence"] + "; " if entry["evidence"] else "") + \
                f"missed assessment questions on it {n} time(s)"
        return sorted(scores.values(), key=lambda x: -x["score"])[:4]

    # ------------------------------------------------------- curriculum
    def _units(self, cur, languages: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        cur.execute("""
        SELECT c.id AS course_id, c.title AS course_title, c.language, lv.id AS level_id, lv.level_number,
               lv.title AS level_title, t.id AS task_id, t.title AS task_title, t.kind, t.task_type, t.concept AS task_concept,
               t.difficulty, t.estimated_minutes AS task_minutes, t.prompt, t.sort_order,
               l.id AS lesson_id, l.title AS lesson_title, l.summary, l.concept AS lesson_concept,
               l.estimated_minutes AS lesson_minutes
        FROM courses c
        JOIN course_levels lv ON lv.course_id = c.id
        JOIN course_tasks t ON t.level_id = lv.id
        LEFT JOIN course_lessons l ON l.id = t.lesson_id
        WHERE c.language = ANY(%s)
        ORDER BY c.sort_order, lv.level_number, t.sort_order;
        """, (languages,))
        by_course: Dict[str, List[Dict[str, Any]]] = {}
        for r in cur.fetchall():
            by_course.setdefault(r["course_id"], []).append(dict(r))
        return by_course

    # --------------------------------------------------------- generate
    async def generate(self, conn: psycopg.Connection, user_id: str, track: str) -> Dict[str, Any]:
        cur = conn.cursor()
        languages = TRACK_LANGUAGES[track]
        signals = self._signals(cur, user_id)
        priorities = self._priority_concepts(signals)
        priority_names = {p["concept"] for p in priorities}
        difficulty_mode = adaptive_engine.get_practice_difficulty(conn, user_id)

        cur.execute("SELECT item_id FROM course_completions WHERE user_id = %s AND item_type = 'task';", (user_id,))
        done_tasks = {r["item_id"] for r in cur.fetchall()}

        # Review days already rewarded in the last 7 days are not offered again (no XP farming by regenerating).
        cur.execute("""
        SELECT d.linked_id FROM roadmap_days d JOIN learning_roadmaps r ON r.id = d.roadmap_id
        WHERE r.user_id = %s AND d.day_type = 'review' AND d.completed_at > now() - interval '7 days';
        """, (user_id,))
        recently_reviewed = {r["linked_id"] for r in cur.fetchall()}

        units_by_course = self._units(cur, languages)
        pending_streams = [[u for u in units if u["task_id"] not in done_tasks] for units in units_by_course.values()]
        completed_units = [u for units in units_by_course.values() for u in units if u["task_id"] in done_tasks]

        # Interleave courses for the mixed track (keeps each course's own prerequisite order)
        pending: List[Dict[str, Any]] = []
        idx = 0
        while any(pending_streams):
            stream = pending_streams[idx % len(pending_streams)]
            if stream:
                pending.append(stream.pop(0))
            idx += 1

        # Review units: already-completed tasks whose concept the student keeps getting wrong
        reviews = []
        for p in priorities:
            match = next((u for u in completed_units
                          if (u["lesson_concept"] == p["concept"] or u["task_concept"] == p["concept"])
                          and u["kind"] == "practice" and u["task_id"] not in recently_reviewed
                          and u["task_id"] not in {r["unit"]["task_id"] for r in reviews}), None)
            if match:
                reviews.append({"unit": match, "priority": p})

        # Challenge days for weak skills from the existing adaptive engine
        challenge_days = []
        for skill in signals["weak_skills"][:3]:
            cur.execute("""
            SELECT c.id, c.title, c.topic, c.difficulty, c.description FROM coding_challenges c
            WHERE c.topic = %s AND (c.visibility = 'public' OR c.created_by = %s) AND NOT EXISTS (
                SELECT 1 FROM code_submissions s WHERE s.user_id = %s AND s.challenge_id = c.id AND s.status = 'Accepted')
            ORDER BY c.xp_reward LIMIT 1;
            """, (skill["skill_name"], user_id, user_id))
            ch = cur.fetchone()
            if ch and ch["id"] not in {c["challenge"]["id"] for c in challenge_days}:
                challenge_days.append({"challenge": dict(ch), "mastery": skill["mastery_level"]})

        # Assemble the plan
        plan: List[Dict[str, Any]] = []
        front_reviews = 2 if difficulty_mode == "easier" else 1
        for r in reviews[:front_reviews]:
            plan.append(self._review_day(r))
        rest_reviews = reviews[front_reviews:]
        for u in pending:
            plan.append(self._unit_day(u, priority_names))
            n = len(plan)
            if n % 7 == 0 and challenge_days:
                plan.append(self._challenge_day(challenge_days.pop(0)))
            elif n % 6 == 0 and rest_reviews:
                plan.append(self._review_day(rest_reviews.pop(0)))
            if len(plan) >= ROADMAP_DAYS:
                break
        for extra in [self._challenge_day(c) for c in challenge_days] + [self._review_day(r) for r in rest_reviews]:
            if len(plan) >= ROADMAP_DAYS:
                break
            plan.append(extra)
        plan = plan[:ROADMAP_DAYS]

        focus, tips, generated_with = await self._narrative(signals, priorities, plan, track, difficulty_mode)

        # Persist: archive the old active plan, insert the new one
        cur.execute("UPDATE learning_roadmaps SET status = 'archived' WHERE user_id = %s AND status = 'active';", (user_id,))
        roadmap_id = str(uuid.uuid4())
        cur.execute("""
        INSERT INTO learning_roadmaps (id, user_id, track, status, focus_summary, priority_concepts, generated_with)
        VALUES (%s, %s, %s, 'active', %s, %s, %s);
        """, (roadmap_id, user_id, track, focus, json.dumps(priorities), generated_with))
        for i, day in enumerate(plan, start=1):
            cur.execute("""
            INSERT INTO roadmap_days (id, roadmap_id, day_number, day_type, topic, objective, explanation, task_description,
                difficulty, estimated_minutes, xp_reward, reason, coach_tip, course_id, lesson_id, linked_type, linked_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (str(uuid.uuid4()), roadmap_id, i, day["day_type"], day["topic"], day["objective"], day["explanation"],
                  day["task_description"], day["difficulty"], day["estimated_minutes"], day["xp_reward"], day["reason"],
                  tips[i - 1] if i - 1 < len(tips) else None, day.get("course_id"), day.get("lesson_id"),
                  day["linked_type"], day["linked_id"]))
        return self.get_active(conn, user_id, sync=False)

    def _unit_day(self, u: Dict[str, Any], priority_names) -> Dict[str, Any]:
        if u["kind"] == "practice":
            concept = u["lesson_concept"] or u["task_concept"]
            reason = f"Next step in {u['course_title']}, Level {u['level_number']} ({u['level_title']})."
            if concept in priority_names:
                reason += f" Extra care: {concept} is one of your current focus areas."
            return {
                "day_type": "lesson",
                "topic": u["lesson_title"] or u["task_title"],
                "objective": f"Understand {concept} and apply it by completing '{u['task_title']}'.",
                "explanation": u["summary"] or u["prompt"][:300],
                "task_description": f"Read the lesson '{u['lesson_title']}', then complete the practice task '{u['task_title']}'.",
                "difficulty": u["difficulty"],
                "estimated_minutes": (u["lesson_minutes"] or 0) + (u["task_minutes"] or 0),
                "xp_reward": DAY_XP["lesson"],
                "reason": reason,
                "course_id": u["course_id"], "lesson_id": u["lesson_id"],
                "linked_type": "course_task", "linked_id": u["task_id"],
            }
        return {
            "day_type": "assessment",
            "topic": u["task_title"],
            "objective": f"Show you have mastered Level {u['level_number']}: {u['level_title']}.",
            "explanation": f"The {'final course' if u['kind'] == 'final' else 'level'} assessment checks every lesson in this level. Passing it unlocks the next level.",
            "task_description": f"Pass '{u['task_title']}' in the {u['course_title']} course.",
            "difficulty": u["difficulty"],
            "estimated_minutes": u["task_minutes"] or 15,
            "xp_reward": DAY_XP["assessment"],
            "reason": f"Completes Level {u['level_number']} of {u['course_title']}.",
            "course_id": u["course_id"], "lesson_id": None,
            "linked_type": "course_task", "linked_id": u["task_id"],
        }

    def _review_day(self, r: Dict[str, Any]) -> Dict[str, Any]:
        u, p = r["unit"], r["priority"]
        return {
            "day_type": "review",
            "topic": f"Review: {u['lesson_title'] or u['task_title']}",
            "objective": f"Strengthen {p['concept']} - the concept behind your recent mistakes.",
            "explanation": u["summary"] or "",
            "task_description": f"Re-read the lesson, then solve '{u['task_title']}' again without hints.",
            "difficulty": u["difficulty"],
            "estimated_minutes": max(15, (u["task_minutes"] or 15)),
            "xp_reward": DAY_XP["review"],
            "reason": f"Personalised review: {p['evidence']}.",
            "course_id": u["course_id"], "lesson_id": u["lesson_id"],
            "linked_type": "course_task", "linked_id": u["task_id"],
        }

    def _challenge_day(self, c: Dict[str, Any]) -> Dict[str, Any]:
        ch = c["challenge"]
        return {
            "day_type": "challenge",
            "topic": f"Practice challenge: {ch['title']}",
            "objective": f"Raise your {ch['topic']} mastery with a {ch['difficulty'].lower()} challenge.",
            "explanation": ch["description"][:300],
            "task_description": f"Solve the '{ch['title']}' challenge in the Playground until all test cases pass.",
            "difficulty": ch["difficulty"],
            "estimated_minutes": 20,
            "xp_reward": DAY_XP["challenge"],
            "reason": f"Your {ch['topic']} mastery is {c['mastery']:.0f}% - below the 50% target.",
            "course_id": None, "lesson_id": None,
            "linked_type": "challenge", "linked_id": ch["id"],
        }

    async def _narrative(self, signals, priorities, plan, track, difficulty_mode):
        track_name = {"c": "C Programming", "sql": "DBMS & SQL", "mixed": "C Programming and DBMS & SQL"}[track]
        if priorities:
            focus = (f"Your plan prioritises {', '.join(p['concept'] for p in priorities[:3])}, based on your recorded mistakes "
                     f"and assessment results, while continuing through {track_name}.")
        else:
            focus = (f"No recurring weak spots recorded yet, so your plan follows the {track_name} curriculum from where you are. "
                     f"It will adapt as you practise.")
        if difficulty_mode == "easier":
            focus += " Recent attempts have been tough, so the plan opens with consolidation before new material."
        if not plan:
            focus = "You have completed every lesson and task in this track. Regenerate with another track or keep practising challenges."

        system = (
            "You are a study coach. Write an encouraging, specific focus summary and short daily tips for a 30-day plan. "
            "Use ONLY the facts provided. Do not invent scores, completions or progress. "
            'Reply with JSON: {"focus_summary": "2-3 sentences", "tips": ["one short tip per listed day, in order"]}'
        )
        facts = {
            "track": track_name,
            "priority_concepts": [{"concept": p["concept"], "evidence": p["evidence"]} for p in priorities],
            "recent_accuracy_percent": signals["recent_accuracy"],
            "recent_graded_attempts": signals["recent_attempts"],
            "first_days": [{"day": i + 1, "topic": d["topic"], "type": d["day_type"]} for i, d in enumerate(plan[:7])],
        }
        data = await ai_mentor_service.generate_json(system, json.dumps(facts), ["focus_summary"])
        if data and isinstance(data.get("tips", []), list):
            tips = [str(t)[:240] for t in data.get("tips", [])[:7] if isinstance(t, (str, int, float))]
            return str(data["focus_summary"])[:600], tips, "rules+llm"
        return focus, [], "rules"

    # ------------------------------------------------------------- read
    def get_active(self, conn: psycopg.Connection, user_id: str, sync: bool = True) -> Optional[Dict[str, Any]]:
        if sync:
            self.sync_progress(conn, user_id)
        cur = conn.cursor()
        cur.execute("SELECT * FROM learning_roadmaps WHERE user_id = %s AND status = 'active';", (user_id,))
        rm = cur.fetchone()
        if not rm:
            return None
        cur.execute("""
        SELECT d.*, c.slug AS course_slug, c.title AS course_title FROM roadmap_days d
        LEFT JOIN courses c ON c.id = d.course_id
        WHERE d.roadmap_id = %s ORDER BY d.day_number;
        """, (rm["id"],))
        days = []
        for d in cur.fetchall():
            days.append({
                "id": d["id"], "day_number": d["day_number"], "day_type": d["day_type"], "topic": d["topic"],
                "objective": d["objective"], "explanation": d["explanation"], "task_description": d["task_description"],
                "difficulty": d["difficulty"], "estimated_minutes": d["estimated_minutes"], "xp_reward": d["xp_reward"],
                "reason": d["reason"], "coach_tip": d["coach_tip"], "course_slug": d["course_slug"],
                "course_title": d["course_title"], "lesson_id": d["lesson_id"], "linked_type": d["linked_type"],
                "linked_id": d["linked_id"], "completed": d["completed_at"] is not None,
                "completed_at": d["completed_at"].isoformat() if d["completed_at"] else None,
                "scheduled_date": (rm["start_date"] + timedelta(days=d["day_number"] - 1)).isoformat(),
            })
        completed = sum(1 for d in days if d["completed"])
        current = next((d for d in days if not d["completed"]), None)
        return {
            "id": rm["id"], "track": rm["track"], "focus_summary": rm["focus_summary"],
            "priority_concepts": json.loads(rm["priority_concepts"] or "[]"),
            "generated_with": rm["generated_with"], "start_date": rm["start_date"].isoformat(),
            "created_at": rm["created_at"].isoformat(), "days": days, "total_days": len(days),
            "completed_days": completed,
            "percent": round(100.0 * completed / len(days), 1) if days else 0.0,
            "current_day": current,
            "xp_earned": sum(d["xp_reward"] for d in days if d["completed"]),
        }

    # ---------------------------------------------------- verification
    def _verified(self, cur, user_id: str, day: Dict[str, Any], roadmap_created: datetime) -> bool:
        if day["linked_type"] == "challenge":
            cur.execute("""
            SELECT 1 FROM code_submissions WHERE user_id = %s AND challenge_id = %s AND status = 'Accepted' LIMIT 1;
            """, (user_id, day["linked_id"]))
            return cur.fetchone() is not None
        if day["day_type"] == "review":
            cur.execute("""
            SELECT 1 FROM practice_attempts
            WHERE user_id = %s AND context_type = 'course_task' AND context_id = %s AND passed = TRUE AND created_at > %s
            LIMIT 1;
            """, (user_id, day["linked_id"], roadmap_created))
            return cur.fetchone() is not None
        cur.execute("""
        SELECT 1 FROM course_completions WHERE user_id = %s AND item_type = 'task' AND item_id = %s;
        """, (user_id, day["linked_id"]))
        return cur.fetchone() is not None

    def sync_progress(self, conn: psycopg.Connection, user_id: str) -> List[Dict[str, Any]]:
        """Marks every verifiably-finished day complete and awards its XP exactly once."""
        cur = conn.cursor()
        cur.execute("SELECT id, created_at FROM learning_roadmaps WHERE user_id = %s AND status = 'active';", (user_id,))
        rm = cur.fetchone()
        if not rm:
            return []
        cur.execute("SELECT * FROM roadmap_days WHERE roadmap_id = %s AND completed_at IS NULL ORDER BY day_number;", (rm["id"],))
        newly = []
        for day in cur.fetchall():
            if not self._verified(cur, user_id, day, rm["created_at"]):
                continue
            cur.execute("""
            UPDATE roadmap_days SET completed_at = now() WHERE id = %s AND completed_at IS NULL RETURNING day_number;
            """, (day["id"],))
            if cur.fetchone():
                adaptive_engine.award_xp(conn, user_id, day["xp_reward"], "roadmap_day_completed",
                                         {"roadmap_id": rm["id"], "day": day["day_number"], "topic": day["topic"]})
                newly.append({"day_number": day["day_number"], "topic": day["topic"], "xp_earned": day["xp_reward"]})
        return newly

    def complete_day(self, conn: psycopg.Connection, user_id: str, day_id: str) -> Dict[str, Any]:
        cur = conn.cursor()
        cur.execute("""
        SELECT d.*, r.user_id FROM roadmap_days d JOIN learning_roadmaps r ON r.id = d.roadmap_id
        WHERE d.id = %s AND r.user_id = %s AND r.status = 'active';
        """, (day_id, user_id))
        day = cur.fetchone()
        if not day:
            return {"completed": False, "status_code": 404, "message": "Roadmap day not found."}
        if day["completed_at"]:
            return {"completed": True, "already_completed": True, "xp_earned": 0,
                    "message": "This day is already complete. XP is only awarded once."}
        newly = self.sync_progress(conn, user_id)
        mine = next((n for n in newly if n["day_number"] == day["day_number"]), None)
        if mine:
            return {"completed": True, "already_completed": False, "xp_earned": mine["xp_earned"],
                    "other_days_completed": [n for n in newly if n is not mine],
                    "message": f"Day {day['day_number']} verified and completed."}
        need = {
            "review": "Solve the linked task again (a passing attempt made after this roadmap was created).",
            "challenge": "Pass every test case of the linked challenge in the Playground.",
        }.get(day["day_type"], "Complete the linked Coding Academy task - it is verified when it passes.")
        return {"completed": False, "already_completed": False, "xp_earned": 0,
                "message": f"Not verified yet. {need}"}


roadmap_service = RoadmapService()
