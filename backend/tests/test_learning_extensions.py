"""
End-to-end tests for the learning extensions (Scenarios 1-6 and 8 of the spec).

Runs against the real Supabase database and Judge0 through the FastAPI app.
A throwaway student (qa-<uuid>@dbce.test) is created and DELETED at the end;
ON DELETE CASCADE removes every row it produced.

Run:  .venv\\Scripts\\python.exe backend\\tests\\test_learning_extensions.py
"""
import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from httpx import ASGITransport, AsyncClient

from app.academy.content import COURSES
from app.database.session import get_db, init_database
from app.main import app

PASSED = []


def ok(name: str, cond: bool, detail: str = ""):
    if not cond:
        raise AssertionError(f"FAILED: {name} {detail}")
    PASSED.append(name)
    print(f"  [PASS] {name}")


def task_index():
    idx = {}
    for course in COURSES:
        for level in course["levels"]:
            for lesson in level["lessons"]:
                idx[lesson["task"]["id"]] = dict(lesson["task"], lesson_id=lesson["id"], course=course["id"], level=level["number"])
            a = level["assessment"]
            idx[a["id"]] = dict(a, type="quiz", lesson_id=None, course=course["id"], level=level["number"])
    return idx


TASKS = task_index()


def correct_payload(task_id: str):
    t = TASKS[task_id]
    if t["type"] == "code":
        return {"code": t["solution"]}
    if t["type"] == "sql":
        return {"code": t["reference_sql"]}
    return {"answers": [q["answer"] for q in t["questions"]]}


async def profile_xp(c, h):
    r = await c.get("/api/auth/me", headers=h)
    return r.json()["total_xp"]


async def main():
    init_database()
    email = f"qa-{uuid.uuid4().hex[:10]}@dbce.test"
    user_id = None
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=120) as c:
        try:
            r = await c.post("/api/auth/register", json={"email": email, "password": "QaPassword123!", "full_name": "QA Student"})
            ok("register test student", r.status_code == 200, r.text)
            token = r.json()["access_token"]
            user_id = r.json()["user"]["id"]
            h = {"Authorization": f"Bearer {token}"}

            # ---------------- Coding Academy basics ----------------
            print("\nScenario 2/3 - Coding Academy structure")
            r = await c.get("/api/academy/courses", headers=h)
            courses = r.json()
            ok("exactly two MVP courses", len(courses) == 2 and {x["slug"] for x in courses} == {"c-programming", "dbms-sql"})
            r = await c.get("/api/academy/courses/c-programming", headers=h)
            cdet = r.json()
            ok("C course has 5 levels, level 1 unlocked, level 2 locked",
               len(cdet["levels"]) == 5 and cdet["levels"][0]["unlocked"] and not cdet["levels"][1]["unlocked"])
            r = await c.get("/api/academy/tasks/c_t1_hello", headers=h)
            t = r.json()
            ok("task API hides solution / reference / answers",
               "solution_code" not in t and "reference_sql" not in t and "solution" not in str(t.keys()))
            r = await c.get("/api/academy/tasks/c_a1", headers=h)
            ok("quiz questions are served without the answer key", all("answer" not in q for q in r.json()["questions"]))
            r = await c.post("/api/academy/tasks/c_a1/submit", headers=h, json=correct_payload("c_a1"))
            ok("assessment locked until practice tasks are done", r.status_code == 403, r.text)
            r = await c.post("/api/academy/tasks/c_t4_evenodd/submit", headers=h, json=correct_payload("c_t4_evenodd"))
            ok("level 2 task locked before level 1 assessment", r.status_code == 403)

            # ---------------- Scenario 8: lesson XP once ----------------
            print("\nScenario 8 - XP integrity")
            xp0 = await profile_xp(c, h)
            r1 = (await c.post("/api/academy/lessons/c_l1_intro/complete", headers=h)).json()
            r2 = (await c.post("/api/academy/lessons/c_l1_intro/complete", headers=h)).json()
            ok("lesson awards XP once", r1["xp_earned"] == 10 and r2["xp_earned"] == 0, f"{r1} {r2}")
            ok("profile XP increased by exactly 10", await profile_xp(c, h) == xp0 + 10)

            r = (await c.post("/api/academy/tasks/c_t1_hello/submit", headers=h, json={"code": "#include <stdio.h>\nint main(void){ printf(\"Hello C\\n\"); return 0; }"})).json()
            ok("wrong C output is rejected (verified by Judge0)", not r["passed"] and r["xp_earned"] == 0, r["status"])
            r = (await c.post("/api/academy/tasks/c_t1_hello/submit", headers=h, json=correct_payload("c_t1_hello"))).json()
            ok("correct C program passes and earns task XP", r["passed"] and r["xp_earned"] == 25, str(r.get("status")))
            r = (await c.post("/api/academy/tasks/c_t1_hello/submit", headers=h, json=correct_payload("c_t1_hello"))).json()
            ok("re-submitting a completed task earns no XP", r["passed"] and r["xp_earned"] == 0 and r["already_completed"])

            # ---------------- Scenario 4: repeated mistake ----------------
            print("\nScenario 4 - Repeated mistake detection (Deja Vu)")
            bad_scanf = "#include <stdio.h>\nint main(void){ int a, b; scanf(\"%d %d\", a, b); printf(\"%d\\n\", a + b); return 0; }"
            r1 = (await c.post("/api/academy/tasks/c_t2_sum/submit", headers=h, json={"code": bad_scanf})).json()
            ok("first scanf mistake is stored as first-time", r1["deja_vu"]["status"] == "first_time"
               and r1["deja_vu"]["current"]["signature"] in ("c:scanf-missing-ampersand", "c:invalid-memory-access"), str(r1["deja_vu"]))
            first_sig = r1["deja_vu"]["current"]["signature"]
            first_occ = r1["deja_vu"]["occurrence_id"]
            r2 = (await c.post("/api/academy/tasks/c_t2_sum/submit", headers=h, json={"code": bad_scanf})).json()
            ok("same mistake again is detected as a repeat", r2["deja_vu"]["status"] == "repeat"
               and r2["deja_vu"]["previous"] is not None and r2["deja_vu"]["current"]["signature"] == first_sig)
            ok("repeat shows previous mistake, concept, correction and recommendation",
               all(k in r2["deja_vu"] for k in ("previous", "related_concept", "recommendation"))
               and r2["deja_vu"]["previous"]["suggested_correction"])
            r3 = (await c.post("/api/academy/tasks/c_t3_divmod/submit", headers=h, json={"code": "#include <stdio.h>\nint main(void){ int a, b; scanf(\"%d %d\", &a, &b); printf(\"%d %d\\n\", a % b, a / b) return 0; }"})).json()
            ok("an unrelated mistake is NOT reported as a repeat", r3["deja_vu"]["status"] != "repeat"
               and r3["deja_vu"]["current"]["signature"] == "c:missing-semicolon", str(r3["deja_vu"]["current"]))
            r = (await c.post("/api/academy/tasks/c_t2_sum/submit", headers=h, json=correct_payload("c_t2_sum"))).json()
            ok("fixing the task passes", r["passed"])
            mem = (await c.get("/api/memory/patterns", headers=h)).json()
            pat = next(p for p in mem["patterns"] if p["signature"] == first_sig)
            ok("pattern stores repetitions and the student's own fix",
               pat["occurrences"] == 2 and pat["resolved_count"] >= 1 and pat["recent_occurrences"][0]["fixed_code_snippet"])

            # ---------------- Scenario 5: Memory Replay ----------------
            print("\nScenario 5 - Memory Replay")
            ok("a mistake sharing a concept with an earlier one is 'related', not 'repeat'",
               r3["deja_vu"]["status"] == "related", r3["deja_vu"]["status"])
            fresh = (await c.post("/api/academy/tasks/sql_t2_select_all/submit", headers=h,
                                  json={"code": "SELECT nme FROM departments;"})).json()
            ok("SQL unknown column classified", fresh["deja_vu"]["current"]["signature"] == "sql:unknown-column")
            rep = (await c.post("/api/memory/replay", headers=h, json={"occurrence_id": fresh["deja_vu"]["occurrence_id"]})).json()
            ok("first-time mistake shows first-time state, no fake personalisation",
               rep["first_time"] and rep["personalized"] is None and rep["generic"]["explanation"], str(rep)[:300])
            rep = (await c.post("/api/memory/replay", headers=h, json={"occurrence_id": r2["deja_vu"]["occurrence_id"]})).json()
            ok("repeated mistake gets personalised feedback using memory",
               not rep["first_time"] and rep["personalized"] and len(rep["memory_used"]) >= 1)
            ok("personalised feedback differs from generic",
               rep["personalized"]["explanation"] != rep["generic"]["explanation"])
            print(f"     (generic source: {rep['generic']['source']}, personalised source: {rep['personalized']['source']})")
            other = await c.post("/api/memory/replay", headers={"Authorization": "Bearer invalid"}, json={"occurrence_id": first_occ})
            ok("replay requires authentication", other.status_code == 401)

            # ---------------- Scenario 6: strain + hints ----------------
            print("\nScenario 6 - Learning strain and progressive hints")
            wrong_div = "#include <stdio.h>\nint main(void){ int a, b; scanf(\"%d %d\", &a, &b); printf(\"%d %d\\n\", a % b, a / b); return 0; }"
            last = None
            for i in range(3):
                last = (await c.post("/api/academy/tasks/c_t3_divmod/submit", headers=h, json={"code": wrong_div})).json()
            a = last["assistance"]
            ok("3+ consecutive failures raise strain and offer a hint",
               a["offer_hint"] and a["strain_score"] >= 45 and a["consecutive_failures"] >= 3, str(a))
            ok("strain lists measurable signals and a non-medical disclaimer",
               any(s["signal"] == "consecutive_failures" for s in a["signals"]) and "not a medical" in a["disclaimer"])
            await c.post("/api/assist/respond", headers=h, json={"context_type": "course_task", "context_id": "c_t3_divmod", "accepted": False})
            nxt = (await c.post("/api/academy/tasks/c_t3_divmod/submit", headers=h, json={"code": wrong_div})).json()
            ok("after dismissing, the offer pauses (no repeated interruption)", not nxt["assistance"]["offer_hint"])
            nxt = (await c.post("/api/academy/tasks/c_t3_divmod/submit", headers=h, json={"code": wrong_div})).json()
            ok("offer returns after 2 more failures", nxt["assistance"]["offer_hint"])
            levels = []
            for i in range(3):
                hr = (await c.post("/api/assist/hint", headers=h, json={"context_type": "course_task", "context_id": "c_t3_divmod", "code": wrong_div})).json()
                levels.append(hr["level"])
                ok(f"hint {i + 1} is level {i + 1} ({hr['level_name']}, source={hr['source']}) and is not the full solution",
                   hr["level"] == i + 1 and hr["hint"] and "printf(\"%d %d\\n\", a / b, a % b)" not in hr["hint"], hr.get("hint", ""))
            hr = (await c.post("/api/assist/hint", headers=h, json={"context_type": "course_task", "context_id": "c_t3_divmod"})).json()
            ok("after 3 hints, hints are exhausted and recovery is suggested",
               hr["exhausted"] and any(x["type"] == "easier_problem" or x["type"] == "review" for x in hr["recovery"]))
            st = (await c.get("/api/assist/strain", headers=h, params={"context_type": "course_task", "context_id": "c_t3_divmod"})).json()
            ok("high strain includes break/review/easier-problem recovery", len(st["recovery"]) >= 2, str(st["recovery"]))
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) AS n FROM hint_history WHERE user_id = %s;", (user_id,))
                hcount = cur.fetchone()["n"]
                cur.execute("SELECT COUNT(*) AS n FROM ai_feedback WHERE user_id = %s AND mode = 'hint';", (user_id,))
                fcount = cur.fetchone()["n"]
            ok("hint usage is recorded (hint_history + existing ai_feedback for DNA)", hcount == 3 and fcount == 3)
            r = (await c.post("/api/assist/hint", headers=h, json={"context_type": "course_task", "context_id": "c_a1"}))
            ok("hints are refused during assessments", r.status_code == 400)
            r = (await c.post("/api/academy/tasks/c_t3_divmod/submit", headers=h, json=correct_payload("c_t3_divmod"))).json()
            ok("student recovers and passes", r["passed"])

            # ---------------- Scenario 1: roadmap ----------------
            print("\nScenario 1 - Personalised roadmap")
            r = (await c.post("/api/roadmap/generate", headers=h, json={"track": "mixed"})).json()["roadmap"]
            ok("roadmap generated with up to 30 days", r and 1 <= r["total_days"] <= 30, str(r and r["total_days"]))
            ok("roadmap prioritises the student's recorded weak concepts",
               any(p["concept"] in ("Input/Output", "Operators", "Program Structure", "Pointers & Memory") for p in r["priority_concepts"]),
               str(r["priority_concepts"]))
            day1 = r["days"][0]
            ok("day 1 is a personalised review of a mistake-prone concept", day1["day_type"] == "review" and "Personalised review" in day1["reason"], str(day1))
            ok("every day has topic, objective, explanation, task, difficulty, minutes, XP",
               all(d["topic"] and d["objective"] and d["task_description"] and d["difficulty"] and d["estimated_minutes"] and d["xp_reward"] for d in r["days"]))
            ok("completed tasks are not re-scheduled as new lessons",
               not any(d["day_type"] == "lesson" and d["linked_id"] in ("c_t1_hello", "c_t2_sum", "c_t3_divmod") for d in r["days"]))
            print(f"     (generated_with: {r['generated_with']}; focus: {r['focus_summary'][:110]}...)")
            res = (await c.post(f"/api/roadmap/days/{day1['id']}/complete", headers=h)).json()
            ok("unverified day cannot be completed", not res["completed"] and res["xp_earned"] == 0)
            xp_before = await profile_xp(c, h)
            await c.post(f"/api/academy/tasks/{day1['linked_id']}/submit", headers=h, json=correct_payload(day1["linked_id"]))
            r = (await c.get("/api/roadmap", headers=h)).json()["roadmap"]
            ok("review day verified automatically after re-solving", r["days"][0]["completed"])
            ok("roadmap XP awarded once via the existing XP system", await profile_xp(c, h) == xp_before + day1["xp_reward"])
            res = (await c.post(f"/api/roadmap/days/{day1['id']}/complete", headers=h)).json()
            ok("completing the same day again awards nothing", res["already_completed"] and res["xp_earned"] == 0)
            ok("next task is the first incomplete day", r["current_day"]["day_number"] == 2)

            # ---------------- Scenario 2: finish the C course ----------------
            print("\nScenario 2 - Complete the C Programming course")
            for course_id, slug in (("course_c", "c-programming"), ("course_sql", "dbms-sql")):
                course = next(cc for cc in COURSES if cc["id"] == course_id)
                badge = None
                for level in course["levels"]:
                    for lesson in level["lessons"]:
                        await c.post(f"/api/academy/lessons/{lesson['id']}/complete", headers=h)
                        tid = lesson["task"]["id"]
                        rr = (await c.post(f"/api/academy/tasks/{tid}/submit", headers=h, json=correct_payload(tid))).json()
                        assert rr.get("passed"), f"{tid} did not pass: {rr}"
                    aid = level["assessment"]["id"]
                    if level["number"] == 2 and course_id == "course_sql":
                        bad = (await c.post(f"/api/academy/tasks/{aid}/submit", headers=h, json={"answers": [0, 0, 0, 0]})).json()
                        ok("failed assessment does not reveal the answer key",
                           not bad["passed"] and all("correct_option" not in q for q in bad["details"]["questions"]))
                    rr = (await c.post(f"/api/academy/tasks/{aid}/submit", headers=h, json=correct_payload(aid))).json()
                    assert rr["passed"] and rr["level_completed"], f"{aid}: {rr}"
                    if rr.get("badge_awarded"):
                        badge = rr["badge_awarded"]
                    if level["number"] == 5:
                        ok(f"{course['title']}: final assessment completes the course", rr["course_completed"])
                ok(f"{course['title']}: completion badge awarded", badge is not None and badge["course_title"] == course["title"], str(badge))
                again = (await c.post(f"/api/academy/tasks/{course['levels'][4]['assessment']['id']}/submit", headers=h,
                                      json=correct_payload(course["levels"][4]["assessment"]["id"]))).json()
                ok(f"{course['title']}: badge and course XP not awarded twice", again["badge_awarded"] is None and again["xp_earned"] == 0)
                det = (await c.get(f"/api/academy/courses/{slug}", headers=h)).json()
                ok(f"{course['title']}: progress is 100% and course marked complete", det["completed"] and det["progress"]["percent"] == 100.0)
                if course_id == "course_c":
                    print("\nScenario 3 - Complete the DBMS & SQL course")

            cart = (await c.post("/api/academy/tasks/sql_t12_join/submit", headers=h,
                                 json={"code": "SELECT e.name, d.name FROM employees e, departments d ORDER BY e.name;"})).json()
            ok("SQL Cartesian join is rejected (verified result) and classified as a join mistake", not cart["passed"]
               and cart["deja_vu"]["current"]["signature"] == "sql:join-missing-condition", str(cart.get("deja_vu")))
            ok("failing an already-completed task awards no XP", cart["xp_earned"] == 0)

            ach = (await c.get("/api/achievements", headers=h)).json()
            course_badges = [a for a in ach if a["category"] == "course" and a["unlocked"]]
            ok("both course badges appear in Achievements with course name and date",
               len(course_badges) == 2 and all(a["course_title"] and a["unlocked_at"] for a in course_badges))

            # ---------------- Scenario 8: challenge XP & ledger ----------------
            print("\nScenario 8 - Existing challenge XP dedupe and ledger consistency")
            sol = "def sum_numbers(numbers):\n    return sum(numbers)\n"
            s1 = (await c.post("/api/execution/submit", headers=h, json={"challenge_id": "ch_sum_list", "code": sol})).json()
            s2 = (await c.post("/api/execution/submit", headers=h, json={"challenge_id": "ch_sum_list", "code": sol})).json()
            ok("first accepted challenge solution earns XP, the second does not", s1["xp_earned"] == 50 and s2["xp_earned"] == 0)
            ok("challenge submit reports real execution time", s1["execution_seconds"] > 0)
            bad = (await c.post("/api/execution/submit", headers=h, json={"challenge_id": "ch_find_max", "code": "def find_max(numbers):\n    return 0\n"})).json()
            ok("failed challenge returns Deja Vu + assistance (existing response fields intact)",
               bad["deja_vu"] is not None and bad["assistance"] is not None and "test_results" in bad)
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("SELECT total_xp FROM student_profiles WHERE user_id = %s;", (user_id,))
                total = cur.fetchone()["total_xp"]
                cur.execute("SELECT COALESCE(SUM(xp_earned), 0) AS s FROM learning_history WHERE user_id = %s;", (user_id,))
                ledger = cur.fetchone()["s"]
            ok(f"profile XP ({total}) equals the learning_history ledger ({ledger})", total == ledger)
            dash = await c.get("/api/analytics/dashboard", headers=h)
            ok("existing dashboard still works with course skills", dash.status_code == 200 and len(dash.json()["skills"]) > 1)
        finally:
            if user_id:
                with get_db() as conn:
                    conn.cursor().execute("DELETE FROM users WHERE id = %s;", (user_id,))
                print(f"\n  cleanup: deleted test student {email} and all of its data")

    print(f"\nALL {len(PASSED)} LEARNING-EXTENSION CHECKS PASSED")


if __name__ == "__main__":
    asyncio.run(main())
