"""
Coding Academy: course progress, level unlocking, task verification and rewards.

Integrity rules
- XP is only awarded after deterministic verification (Judge0 / SQL sandbox / answer key).
- Every reward goes through INSERT ... ON CONFLICT DO NOTHING RETURNING on
  course_completions (or student_achievements); XP is granted only if a row was
  actually inserted, so repeating a request can never award XP or a badge twice.
- XP itself is applied by the existing adaptive engine (one XP/level/streak system).
"""
import json
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple

import psycopg

from app.academy import grading
from app.adaptive_learning.engine import adaptive_engine
from app.assistance.service import assistance_service
from app.mistake_memory.classifier import classify_c, classify_sql, Mistake, _slug
from app.mistake_memory.service import mistake_memory_service


class AcademyError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class AcademyService:
    # ------------------------------------------------------------ loading
    def _completions(self, cur, user_id: Optional[str], course_id: Optional[str] = None) -> Set[Tuple[str, str]]:
        if not user_id:
            return set()
        if course_id:
            cur.execute("SELECT item_type, item_id FROM course_completions WHERE user_id = %s AND course_id = %s;", (user_id, course_id))
        else:
            cur.execute("SELECT item_type, item_id FROM course_completions WHERE user_id = %s;", (user_id,))
        return {(r["item_type"], r["item_id"]) for r in cur.fetchall()}

    def _structure(self, cur, course_id: str) -> Dict[str, Any]:
        cur.execute("SELECT * FROM course_levels WHERE course_id = %s ORDER BY level_number;", (course_id,))
        levels = cur.fetchall()
        level_ids = [l["id"] for l in levels]
        cur.execute("SELECT * FROM course_lessons WHERE level_id = ANY(%s) ORDER BY sort_order;", (level_ids,))
        lessons = cur.fetchall()
        cur.execute("""
        SELECT id, level_id, lesson_id, sort_order, title, task_type, kind, concept, difficulty, estimated_minutes, xp_reward, pass_mark
        FROM course_tasks WHERE level_id = ANY(%s) ORDER BY sort_order;
        """, (level_ids,))
        tasks = cur.fetchall()
        return {"levels": levels, "lessons": lessons, "tasks": tasks}

    def _level_state(self, structure: Dict[str, Any], done: Set[Tuple[str, str]]) -> Dict[str, Dict[str, Any]]:
        """Unlock rules: level 1 is open; level n opens when level n-1's assessment is passed.
        A level's assessment opens when all of that level's practice tasks are complete."""
        state: Dict[str, Dict[str, Any]] = {}
        prev_passed = True
        for lvl in structure["levels"]:
            practice = [t for t in structure["tasks"] if t["level_id"] == lvl["id"] and t["kind"] == "practice"]
            assessment = next((t for t in structure["tasks"] if t["level_id"] == lvl["id"] and t["kind"] != "practice"), None)
            practice_done = all(("task", t["id"]) in done for t in practice)
            assessment_done = assessment is not None and ("task", assessment["id"]) in done
            state[lvl["id"]] = {
                "unlocked": prev_passed,
                "practice_done": practice_done,
                "assessment_unlocked": prev_passed and practice_done,
                "completed": assessment_done,
                "assessment": assessment,
            }
            prev_passed = assessment_done
        return state

    def _progress(self, structure, done) -> Dict[str, Any]:
        items = [("lesson", l["id"]) for l in structure["lessons"]] + [("task", t["id"]) for t in structure["tasks"]]
        completed = sum(1 for i in items if i in done)
        levels_done = sum(1 for l in structure["levels"] if ("level", l["id"]) in done)
        return {
            "completed_items": completed,
            "total_items": len(items),
            "percent": round(100.0 * completed / len(items), 1) if items else 0.0,
            "levels_completed": levels_done,
            "total_levels": len(structure["levels"]),
        }

    # --------------------------------------------------------- read APIs
    def list_courses(self, conn: psycopg.Connection, user_id: Optional[str]) -> List[Dict[str, Any]]:
        cur = conn.cursor()
        cur.execute("""
        SELECT c.*, a.title AS badge_title, a.badge_icon
        FROM courses c LEFT JOIN achievements a ON a.id = c.completion_achievement_id
        ORDER BY c.sort_order;
        """)
        courses = cur.fetchall()
        all_done = self._completions(cur, user_id)
        out = []
        for c in courses:
            structure = self._structure(cur, c["id"])
            progress = self._progress(structure, all_done)
            state = self._level_state(structure, all_done)
            current_level = next((l for l in structure["levels"] if state[l["id"]]["unlocked"] and not state[l["id"]]["completed"]), None)
            out.append({
                "id": c["id"], "slug": c["slug"], "title": c["title"], "description": c["description"],
                "language": c["language"], "icon": c["icon"], "completion_xp": c["completion_xp"],
                "badge_title": c["badge_title"], "badge_icon": c["badge_icon"],
                "level_titles": [l["title"] for l in structure["levels"]],
                "lesson_count": len(structure["lessons"]),
                "task_count": len(structure["tasks"]),
                "progress": progress,
                "completed": ("course", c["id"]) in all_done,
                "current_level": current_level["level_number"] if current_level else None,
            })
        return out

    def _course_by_slug(self, cur, slug: str) -> Dict[str, Any]:
        cur.execute("""
        SELECT c.*, a.title AS badge_title, a.badge_icon FROM courses c
        LEFT JOIN achievements a ON a.id = c.completion_achievement_id
        WHERE c.slug = %s OR c.id = %s;
        """, (slug, slug))
        course = cur.fetchone()
        if not course:
            raise AcademyError(404, "Course not found")
        return course

    def course_detail(self, conn: psycopg.Connection, slug: str, user_id: Optional[str]) -> Dict[str, Any]:
        cur = conn.cursor()
        course = self._course_by_slug(cur, slug)
        structure = self._structure(cur, course["id"])
        done = self._completions(cur, user_id, course["id"])
        state = self._level_state(structure, done)

        best_scores: Dict[str, float] = {}
        if user_id:
            cur.execute("""
            SELECT item_id, score FROM course_completions WHERE user_id = %s AND course_id = %s AND item_type = 'task';
            """, (user_id, course["id"]))
            best_scores = {r["item_id"]: r["score"] for r in cur.fetchall() if r["score"] is not None}

        levels_out = []
        for lvl in structure["levels"]:
            st = state[lvl["id"]]
            lessons_out = []
            for lesson in [l for l in structure["lessons"] if l["level_id"] == lvl["id"]]:
                task = next((t for t in structure["tasks"] if t["lesson_id"] == lesson["id"]), None)
                lessons_out.append({
                    "id": lesson["id"], "title": lesson["title"], "summary": lesson["summary"],
                    "concept": lesson["concept"], "estimated_minutes": lesson["estimated_minutes"],
                    "xp_reward": lesson["xp_reward"], "completed": ("lesson", lesson["id"]) in done,
                    "task": self._task_brief(task, done) if task else None,
                })
            a = st["assessment"]
            levels_out.append({
                "id": lvl["id"], "level_number": lvl["level_number"], "title": lvl["title"],
                "description": lvl["description"], "unlocked": st["unlocked"], "completed": st["completed"],
                "lessons": lessons_out,
                "assessment": dict(self._task_brief(a, done), unlocked=st["assessment_unlocked"],
                                   best_score=best_scores.get(a["id"])) if a else None,
            })

        return {
            "id": course["id"], "slug": course["slug"], "title": course["title"],
            "description": course["description"], "language": course["language"], "icon": course["icon"],
            "completion_xp": course["completion_xp"], "badge_title": course["badge_title"],
            "badge_icon": course["badge_icon"], "completed": ("course", course["id"]) in done,
            "progress": self._progress(structure, done), "levels": levels_out,
        }

    @staticmethod
    def _task_brief(task: Dict[str, Any], done) -> Dict[str, Any]:
        return {
            "id": task["id"], "title": task["title"], "task_type": task["task_type"], "kind": task["kind"],
            "concept": task["concept"], "difficulty": task["difficulty"],
            "estimated_minutes": task["estimated_minutes"], "xp_reward": task["xp_reward"],
            "pass_mark": task["pass_mark"], "completed": ("task", task["id"]) in done,
        }

    def _load_task(self, cur, task_id: str) -> Dict[str, Any]:
        cur.execute("""
        SELECT t.*, lv.level_number, lv.title AS level_title, lv.course_id,
               c.title AS course_title, c.slug AS course_slug, c.language AS course_language,
               c.completion_xp, c.completion_achievement_id, l.title AS lesson_title
        FROM course_tasks t
        JOIN course_levels lv ON lv.id = t.level_id
        JOIN courses c ON c.id = lv.course_id
        LEFT JOIN course_lessons l ON l.id = t.lesson_id
        WHERE t.id = %s;
        """, (task_id,))
        task = cur.fetchone()
        if not task:
            raise AcademyError(404, "Task not found")
        return task

    def _unlock_status(self, cur, task: Dict[str, Any], user_id: Optional[str]) -> Tuple[bool, str]:
        structure = self._structure(cur, task["course_id"])
        done = self._completions(cur, user_id, task["course_id"])
        st = self._level_state(structure, done)[task["level_id"]]
        if not st["unlocked"]:
            return False, f"Level {task['level_number']} is locked. Pass the Level {task['level_number'] - 1} assessment first."
        if task["kind"] != "practice" and not st["assessment_unlocked"]:
            return False, "Complete all practice tasks in this level to unlock its assessment."
        return True, ""

    def lesson_detail(self, conn: psycopg.Connection, lesson_id: str, user_id: Optional[str]) -> Dict[str, Any]:
        cur = conn.cursor()
        cur.execute("""
        SELECT l.*, lv.level_number, lv.title AS level_title, lv.course_id, c.slug AS course_slug, c.title AS course_title
        FROM course_lessons l JOIN course_levels lv ON lv.id = l.level_id JOIN courses c ON c.id = lv.course_id
        WHERE l.id = %s;
        """, (lesson_id,))
        lesson = cur.fetchone()
        if not lesson:
            raise AcademyError(404, "Lesson not found")
        structure = self._structure(cur, lesson["course_id"])
        done = self._completions(cur, user_id, lesson["course_id"])
        unlocked = self._level_state(structure, done)[lesson["level_id"]]["unlocked"]
        task = next((t for t in structure["tasks"] if t["lesson_id"] == lesson_id), None)
        return {
            "id": lesson["id"], "title": lesson["title"], "summary": lesson["summary"], "content": lesson["content"],
            "concept": lesson["concept"], "estimated_minutes": lesson["estimated_minutes"], "xp_reward": lesson["xp_reward"],
            "level_number": lesson["level_number"], "level_title": lesson["level_title"],
            "course_slug": lesson["course_slug"], "course_title": lesson["course_title"],
            "unlocked": unlocked, "completed": ("lesson", lesson_id) in done,
            "task": self._task_brief(task, done) if task else None,
        }

    def task_detail(self, conn: psycopg.Connection, task_id: str, user_id: Optional[str]) -> Dict[str, Any]:
        """Public view of a task: never includes solutions, reference SQL or quiz answers."""
        cur = conn.cursor()
        task = self._load_task(cur, task_id)
        unlocked, lock_reason = self._unlock_status(cur, task, user_id)
        done = self._completions(cur, user_id, task["course_id"])
        attempts = hints_used = 0
        if user_id:
            cur.execute("SELECT COUNT(*) AS n FROM practice_attempts WHERE user_id = %s AND context_type = 'course_task' AND context_id = %s;", (user_id, task_id))
            attempts = cur.fetchone()["n"]
            cur.execute("SELECT COALESCE(MAX(hint_level), 0) AS n FROM hint_history WHERE user_id = %s AND context_type = 'course_task' AND context_id = %s;", (user_id, task_id))
            hints_used = cur.fetchone()["n"]

        visible_tests = []
        if task["task_type"] == "code":
            visible_tests = [{"stdin": t["stdin"], "expected_output": t["expected_output"]}
                             for t in json.loads(task["test_cases"] or "[]") if not t.get("hidden")]
        hidden_count = 0
        if task["task_type"] == "code":
            hidden_count = sum(1 for t in json.loads(task["test_cases"] or "[]") if t.get("hidden"))

        return {
            "id": task["id"], "title": task["title"], "task_type": task["task_type"], "kind": task["kind"],
            "prompt": task["prompt"], "starter_code": task["starter_code"] or "",
            "concept": task["concept"], "difficulty": task["difficulty"],
            "estimated_minutes": task["estimated_minutes"], "xp_reward": task["xp_reward"],
            "pass_mark": task["pass_mark"], "order_matters": bool(task["order_matters"]),
            "is_modification_task": bool(task["check_sql"]),
            "visible_tests": visible_tests, "hidden_test_count": hidden_count,
            "questions": grading.public_questions(task) if task["task_type"] == "quiz" else [],
            "course_slug": task["course_slug"], "course_title": task["course_title"],
            "course_language": task["course_language"], "level_number": task["level_number"],
            "level_title": task["level_title"], "lesson_id": task["lesson_id"], "lesson_title": task["lesson_title"],
            "unlocked": unlocked, "lock_reason": lock_reason or None,
            "completed": ("task", task_id) in done, "attempts": attempts, "hints_used": hints_used,
            "hints_available": task["kind"] == "practice",
        }

    # -------------------------------------------------------- write APIs
    def complete_lesson(self, conn: psycopg.Connection, lesson_id: str, user_id: str) -> Dict[str, Any]:
        detail = self.lesson_detail(conn, lesson_id, user_id)
        if not detail["unlocked"]:
            raise AcademyError(403, "This lesson's level is locked.")
        cur = conn.cursor()
        cur.execute("SELECT lv.course_id FROM course_lessons l JOIN course_levels lv ON lv.id = l.level_id WHERE l.id = %s;", (lesson_id,))
        course_id = cur.fetchone()["course_id"]
        reward = self._grant(conn, user_id, course_id, "lesson", lesson_id, detail["xp_reward"], None,
                             "academy_lesson_completed", {"lesson_id": lesson_id, "title": detail["title"]})
        from app.roadmap.service import roadmap_service
        roadmap = roadmap_service.sync_progress(conn, user_id)
        return dict(reward, roadmap_days_completed=roadmap)

    def _grant(self, conn, user_id, course_id, item_type, item_id, xp, score, event_type, details) -> Dict[str, Any]:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO course_completions (id, user_id, course_id, item_type, item_id, score, xp_awarded)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id, item_type, item_id) DO NOTHING
        RETURNING id;
        """, (str(uuid.uuid4()), user_id, course_id, item_type, item_id, score, xp))
        inserted = cur.fetchone() is not None
        if inserted and xp > 0:
            res = adaptive_engine.award_xp(conn, user_id, xp, event_type, details)
            return dict(res, newly_completed=True)
        if score is not None and not inserted:
            cur.execute("""
            UPDATE course_completions SET score = GREATEST(COALESCE(score, 0), %s)
            WHERE user_id = %s AND item_type = %s AND item_id = %s;
            """, (score, user_id, item_type, item_id))
        return {"xp_earned": 0, "newly_completed": inserted}

    def run_task(self, conn: psycopg.Connection, task_id: str, user_id: Optional[str], code: str, stdin: str):
        cur = conn.cursor()
        task = self._load_task(cur, task_id)
        if task["task_type"] == "sql":
            return {"kind": "sql", **grading.run_sql_task(task, code)}
        if task["task_type"] == "code":
            return None  # caller awaits run_c_program
        raise AcademyError(400, "Quizzes are answered, not run.")

    async def submit_task(self, conn: psycopg.Connection, task_id: str, user_id: str,
                          code: Optional[str], answers: Optional[List[int]]) -> Dict[str, Any]:
        cur = conn.cursor()
        task = self._load_task(cur, task_id)
        unlocked, reason = self._unlock_status(cur, task, user_id)
        if not unlocked:
            raise AcademyError(403, reason)

        # 1. Deterministic verification
        if task["task_type"] == "code":
            if not (code or "").strip():
                raise AcademyError(400, "Write your C program before submitting.")
            result = await grading.grade_code_task(task, code)
        elif task["task_type"] == "sql":
            if not (code or "").strip():
                raise AcademyError(400, "Write your SQL before submitting.")
            result = grading.grade_sql_task(task, code)
        else:
            if answers is None:
                raise AcademyError(400, "Select an answer for each question.")
            result = grading.grade_quiz(task, answers)

        if result["status"] in ("Task Configuration Error", "Judge0 Not Configured"):
            return {**result, "recorded": False, "xp_earned": 0}

        passed = result["passed"]
        skill_name = f"{task['course_title']}: {task['level_title']}"
        context_title = f"{task['course_title']} · {task['title']}"

        # 2. Mistake Memory + Déjà Vu (failed attempts only)
        deja_vu = None
        signature = None
        if not passed:
            mistake = self._classify(task, code, result)
            if mistake:
                signature = mistake.signature
                comparison = (result.get("details") or {}).get("comparison") or {}
                excerpt = result.get("error") or comparison.get("detail")
                deja_vu = mistake_memory_service.record(
                    conn, user_id, mistake, "course_task", task_id, context_title,
                    code if task["task_type"] != "quiz" else json.dumps(answers),
                    excerpt,
                )
        elif task["task_type"] != "quiz":
            mistake_memory_service.resolve_context(conn, user_id, "course_task", task_id, code or "")

        # 3. Activity record (real timestamps) + skill mastery via the adaptive engine
        assistance_service.record_attempt(conn, user_id, "course_task", task_id, passed, task["concept"],
                                          signature, result.get("execution_seconds") or 0.0)
        adaptive_engine.update_skill(conn, user_id, skill_name, passed)

        # 4. Assessments are recorded in the existing learning_assessments table
        if task["kind"] in ("assessment", "final"):
            details = result.get("details") or {}
            cur.execute("""
            INSERT INTO learning_assessments (id, user_id, topic, calculated_score, strengths, weaknesses, recommended_action)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (str(uuid.uuid4()), user_id, f"{task['course_title']} - Level {task['level_number']}: {task['level_title']}",
                  result.get("score", 0.0), json.dumps(details.get("strong_concepts", [])),
                  json.dumps(details.get("weak_concepts", [])),
                  "Level passed - continue to the next level." if passed else
                  f"Review: {', '.join(details.get('weak_concepts', [])) or task['level_title']} and retry the assessment."))

        # 5. Rewards (only if verified, only once)
        xp_total = 0
        newly_completed = False
        level_completed = False
        course_completed = False
        badge = None
        if passed:
            r = self._grant(conn, user_id, task["course_id"], "task", task_id, task["xp_reward"], result.get("score"),
                            "academy_task_completed", {"task_id": task_id, "title": task["title"], "course": task["course_title"]})
            xp_total += r["xp_earned"]
            newly_completed = r["newly_completed"]
            if task["kind"] in ("assessment", "final"):
                lr = self._grant(conn, user_id, task["course_id"], "level", task["level_id"], 0, None, "academy_level_completed", {})
                level_completed = lr["newly_completed"]
                course_completed, badge, bonus = self._check_course_completion(conn, user_id, task)
                xp_total += bonus

        from app.roadmap.service import roadmap_service
        roadmap_days = roadmap_service.sync_progress(conn, user_id)

        cur.execute("SELECT total_xp, current_level, streak_days FROM student_profiles WHERE user_id = %s;", (user_id,))
        prof = cur.fetchone() or {"total_xp": 0, "current_level": 1, "streak_days": 0}

        # Quizzes: on a failed attempt reveal which questions were wrong, not the answer key.
        if task["task_type"] == "quiz" and not passed and result.get("details"):
            for qf in result["details"]["questions"]:
                qf.pop("correct_option", None)
                if not qf["correct"]:
                    qf["explanation"] = f"Review the lesson on {qf['concept']}."

        assistance = None if passed else assistance_service.compute_strain(conn, user_id, "course_task", task_id)

        return {
            **result,
            "recorded": True,
            "xp_earned": xp_total,
            "already_completed": passed and not newly_completed,
            "level_completed": level_completed,
            "course_completed": course_completed,
            "badge_awarded": badge,
            "new_total_xp": prof["total_xp"],
            "new_level": prof["current_level"],
            "new_streak": prof["streak_days"],
            "deja_vu": deja_vu,
            "assistance": assistance,
            "roadmap_days_completed": roadmap_days,
        }

    def _classify(self, task, code, result) -> Optional[Mistake]:
        if task["task_type"] == "code":
            first_fail = next((t for t in result["test_results"] if not t["passed"] and not t["hidden"]), None)
            err = result.get("error") or ""
            return classify_c(code or "", err if "rror" in result["status"] else "", result["status"], err,
                              task["concept"], first_fail["actual_output"] if first_fail else "",
                              first_fail["expected_output"] if first_fail else "")
        if task["task_type"] == "sql":
            comparison = ((result.get("details") or {}).get("comparison") or {})
            return classify_sql(code or "", result.get("error"), comparison.get("reason"), task["concept"])
        weak = (result.get("details") or {}).get("weak_concepts") or []
        if not weak:
            return None
        concept = weak[0]
        return Mistake(f"quiz:{_slug(concept)}", f"Concept misunderstanding: {concept}", concept, "concept",
                       f"Questions about {concept} were answered incorrectly in '{task['title']}'.",
                       f"Re-read the lesson that covers {concept} and try explaining it in your own words before retrying.")

    def _check_course_completion(self, conn, user_id, task) -> Tuple[bool, Optional[Dict[str, Any]], int]:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS n FROM course_levels WHERE course_id = %s;", (task["course_id"],))
        total_levels = cur.fetchone()["n"]
        cur.execute("""
        SELECT COUNT(*) AS n FROM course_completions WHERE user_id = %s AND course_id = %s AND item_type = 'level';
        """, (user_id, task["course_id"]))
        done_levels = cur.fetchone()["n"]
        cur.execute("""
        SELECT 1 FROM course_completions cc JOIN course_tasks t ON t.id = cc.item_id
        JOIN course_levels lv ON lv.id = t.level_id
        WHERE cc.user_id = %s AND cc.item_type = 'task' AND t.kind = 'final' AND lv.course_id = %s;
        """, (user_id, task["course_id"]))
        final_passed = cur.fetchone() is not None
        if not (final_passed and done_levels >= total_levels):
            return False, None, 0

        r = self._grant(conn, user_id, task["course_id"], "course", task["course_id"], task["completion_xp"], None,
                        "academy_course_completed", {"course": task["course_title"]})
        badge = None
        if task["completion_achievement_id"]:
            cur.execute("""
            INSERT INTO student_achievements (id, user_id, achievement_id) VALUES (%s, %s, %s)
            ON CONFLICT (user_id, achievement_id) DO NOTHING RETURNING unlocked_at;
            """, (str(uuid.uuid4()), user_id, task["completion_achievement_id"]))
            row = cur.fetchone()
            if row:
                cur.execute("SELECT title, description, badge_icon FROM achievements WHERE id = %s;", (task["completion_achievement_id"],))
                a = cur.fetchone()
                badge = {"id": task["completion_achievement_id"], "title": a["title"], "description": a["description"],
                         "badge_icon": a["badge_icon"], "course_title": task["course_title"],
                         "unlocked_at": row["unlocked_at"].isoformat()}
        return r["newly_completed"], badge, r["xp_earned"]


academy_service = AcademyService()
