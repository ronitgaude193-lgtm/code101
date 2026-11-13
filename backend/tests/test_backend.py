import sys
import os
import json

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.session import init_database, get_db
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.execution.service import execution_service
from app.execution.visual_tracer import trace_execution
from app.ai_mentor.service import ai_mentor_service
from app.adaptive_learning.engine import adaptive_engine

def run_all_tests():
    print("=" * 60)
    print("AI CODING MENTOR - BACKEND COMPREHENSIVE AUTOMATED TEST SUITE")
    print("=" * 60)

    # 1. Database Initialization
    print("[TEST 1/8] Initializing database and verifying relational tables...")
    init_database()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) as count FROM coding_challenges;")
        ch_count = cursor.fetchone()["count"]
        assert ch_count >= 5, f"Expected at least 5 seeded challenges, got {ch_count}"
        
        cursor.execute("SELECT count(*) as count FROM achievements;")
        ach_count = cursor.fetchone()["count"]
        assert ach_count >= 6, f"Expected at least 6 seeded achievements, got {ach_count}"
    print(f"  -> SUCCESS: Database initialized with {ch_count} challenges and {ach_count} achievements.")

    # 2. Security & Password Hashing
    print("[TEST 2/8] Testing PBKDF2-SHA256 password hashing & JWT...")
    raw_pw = "MentorSecPass2026!"
    hashed = hash_password(raw_pw)
    assert verify_password(raw_pw, hashed), "Password verification failed"
    assert not verify_password("WrongPass", hashed), "Invalid password was incorrectly verified"

    token = create_access_token({"sub": "student-123", "email": "student@dbce.edu"})
    decoded = decode_access_token(token)
    assert decoded is not None and decoded["sub"] == "student-123", "JWT decode failed"
    print("  -> SUCCESS: Security primitives passed.")

    # 3. Isolated Code Execution
    print("[TEST 3/8] Testing isolated code execution and AST security filter...")
    valid_code = "print('Hello, DBCE Mentor!')\nx = 10 * 5\nprint(f'Computed: {x}')"
    import asyncio
    exec_res = asyncio.run(execution_service.run_code(valid_code))
    assert exec_res["success"], f"Execution failed: {exec_res}"
    assert "Computed: 50" in exec_res["stdout"], "Output mismatch"

    # Test forbidden security import
    forbidden_code = "import os\nos.system('echo hacked')"
    blocked_res = asyncio.run(execution_service.run_code(forbidden_code))
    assert not blocked_res["success"] and "Security Policy Violation" in blocked_res["stderr"]
    print("  -> SUCCESS: Execution sandbox isolated and blocked unauthorized system imports.")

    # 4. Visual Execution Tracing
    print("[TEST 4/8] Testing Visual Execution Tracing (sys.settrace adapter)...")
    trace_code = """
numbers = [2, 4, 6]
total = 0
for n in numbers:
    total += n
print(total)
"""
    trace_res = trace_execution(trace_code)
    assert trace_res["success"], f"Trace failed: {trace_res.get('error')}"
    steps = trace_res["steps"]
    assert len(steps) > 0, "No trace steps returned"
    # Find last step total
    last_vars = [s["variables"] for s in steps if "total" in s["variables"]]
    assert len(last_vars) > 0 and any(v.get("total") == 12 for v in last_vars), "Variable trace mismatch for total"
    print(f"  -> SUCCESS: Visual tracer captured {len(steps)} line/variable event steps.")

    # 5. Challenge Submission & Test Evaluation
    print("[TEST 5/8] Testing challenge submission and adaptive learning engine...")
    test_student_id = "test-student-dna"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (id, email, password_hash, full_name) VALUES (%s, 'dna@dbce.edu', 'hash', 'Test Student') ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email, password_hash = EXCLUDED.password_hash, full_name = EXCLUDED.full_name;", (test_student_id,))
        cursor.execute("INSERT INTO student_profiles (user_id, current_level, total_xp, streak_days) VALUES (%s, 1, 0, 1) ON CONFLICT (user_id) DO UPDATE SET current_level = 1, total_xp = 0, streak_days = 1;", (test_student_id,))

    correct_solution = "def sum_numbers(numbers):\n    return sum(numbers)\n"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT test_cases FROM coding_challenges WHERE id = 'ch_sum_list';")
        tc_json = cursor.fetchone()["test_cases"]

    eval_res = asyncio.run(execution_service.evaluate_challenge("ch_sum_list", correct_solution, tc_json))
    assert eval_res["all_passed"], f"Challenge evaluation failed: {eval_res}"
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO code_submissions (id, user_id, challenge_id, code, language, status, execution_time)
        VALUES ('sub-test-1', %s, 'ch_sum_list', %s, 'python', 'Accepted', 0.05) ON CONFLICT (id) DO NOTHING;
        """, (test_student_id, correct_solution))
        adapt_res = adaptive_engine.record_submission_event(conn, test_student_id, "ch_sum_list", "Accepted", 0.05, None)
    assert adapt_res["xp_earned"] == 50, "XP calculation mismatch"
    assert "First Code Executed" in adapt_res["unlocked_achievements"] or "Bug Hunter" in adapt_res["unlocked_achievements"]
    print("  -> SUCCESS: Challenge submission passed all test cases, updated skills, and awarded XP.")

    # 6. AI Mentor & Pedagogical Fallback
    print("[TEST 6/8] Testing AI Mentor interaction in Learning, Debugging, and Hint modes...")
    mentor_res = asyncio.run(ai_mentor_service.get_mentor_response(
        code="for i in range(len(nums)):\n    total = i",
        mode="debugging"
    ))
    assert mentor_res.summary is not None
    assert len(mentor_res.hints) > 0
    print(f"  -> SUCCESS: AI Mentor generated pedagogical guidance ('{mentor_res.summary}').")

    # 7. AI Code Autopsy (Canonical Misconception Diagnosis)
    print("[TEST 7/8] Testing AI Code Autopsy for loop index vs value confusion...")
    autopsy_code = """
numbers = [2, 4, 6, 8]
total = 0
for i in range(len(numbers)):
    total = i
print(total)
"""
    autopsy_res = asyncio.run(ai_mentor_service.run_code_autopsy(
        code=autopsy_code,
        expected_behavior="Expected total = 20",
        actual_output="Output was 3"
    ))
    assert "Index vs Value" in autopsy_res.misconception_identified or "index" in autopsy_res.primary_failure_reason.lower()
    assert autopsy_res.loop_timeline is not None and len(autopsy_res.loop_timeline) == 4
    print(f"  -> SUCCESS: AI Autopsy successfully identified misconception: {autopsy_res.misconception_identified}.")
    print(f"             Dissected {len(autopsy_res.loop_timeline)} loop iterations explaining state divergences.")

    # 8. Student Dashboard & Programming DNA Profile
    print("[TEST 8/8] Testing Dashboard aggregation & Programming DNA scoring...")
    with get_db() as conn:
        dash = adaptive_engine.get_dashboard_data(conn, test_student_id)
        assert dash.problems_attempted >= 1, "Attempt count mismatch"
        assert dash.problems_solved >= 1, "Solved count mismatch"
        assert dash.programming_dna.overall_dna_archetype is not None
        assert dash.programming_dna.logical_thinking_score > 0
    print(f"  -> SUCCESS: Student Dashboard loaded. Programming DNA Archetype: '{dash.programming_dna.overall_dna_archetype}'.")
    print("=" * 60)
    print("ALL 8 BACKEND TEST MODULES COMPLETED AND PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()
