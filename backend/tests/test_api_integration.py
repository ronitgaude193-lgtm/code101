import sys
import os
import asyncio
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database.session import init_database

async def run_integration_tests():
    print("=" * 60)
    print("AI CODING MENTOR - REST API FULL INTEGRATION TEST SUITE")
    print("=" * 60)
    init_database()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Health Endpoint
        res = await client.get("/api/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        data = res.json()
        print(f"[API TEST 1/10] /api/health OK: Provider = {data['execution_provider']}")

        # 2. Register Student
        reg_payload = {
            "email": "e2e_student@dbce.edu",
            "password": "SecurePassword123!",
            "full_name": "E2E Student Explorer",
            "preferred_language": "python"
        }
        res = await client.post("/api/auth/register", json=reg_payload)
        # If user already registered in prior run, login instead
        if res.status_code == 400:
            login_res = await client.post("/api/auth/login", json={"email": reg_payload["email"], "password": reg_payload["password"]})
            assert login_res.status_code == 200
            token = login_res.json()["access_token"]
        else:
            assert res.status_code == 200, f"Register failed: {res.text}"
            token = res.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        print("[API TEST 2/10] /api/auth/register & login OK: JWT generated")

        # 3. Student Profile /api/auth/me
        res = await client.get("/api/auth/me", headers=auth_headers)
        assert res.status_code == 200
        profile = res.json()
        assert profile["email"] == "e2e_student@dbce.edu"
        print(f"[API TEST 3/10] /api/auth/me OK: Student = {profile['full_name']} (Level {profile['current_level']})")

        # 4. List Challenges /api/challenges
        res = await client.get("/api/challenges", headers=auth_headers)
        assert res.status_code == 200
        challenges = res.json()
        assert len(challenges) >= 5
        ch_id = challenges[0]["id"]
        print(f"[API TEST 4/10] /api/challenges OK: Found {len(challenges)} challenges")

        # 5. Challenge Detail /api/challenges/{id}
        res = await client.get(f"/api/challenges/{ch_id}", headers=auth_headers)
        assert res.status_code == 200
        ch_detail = res.json()
        assert "initial_code" in ch_detail
        print(f"[API TEST 5/10] /api/challenges/{ch_id} OK: '{ch_detail['title']}'")

        # 6. Run Code /api/execution/run
        run_res = await client.post("/api/execution/run", json={"code": "print(2 + 3)", "language": "python"})
        assert run_res.status_code == 200
        assert "5" in run_res.json()["stdout"]
        print("[API TEST 6/10] /api/execution/run OK: Stdout verified")

        # 7. Submit Solution /api/execution/submit
        sub_code = "def sum_numbers(numbers):\n    return sum(numbers)\n"
        sub_res = await client.post("/api/execution/submit", json={"challenge_id": "ch_sum_list", "code": sub_code, "language": "python"}, headers=auth_headers)
        assert sub_res.status_code == 200
        sub_data = sub_res.json()
        assert sub_data["all_passed"]
        print(f"[API TEST 7/10] /api/execution/submit OK: Passed {sub_data['passed_count']}/{sub_data['total_count']} tests, +{sub_data['xp_earned']} XP")

        # 8. Visual Execution Trace /api/execution/trace
        trace_payload = {
            "code": "a = [1, 2]\ntotal = 0\nfor x in a:\n    total += x\nprint(total)",
            "max_steps": 50
        }
        trace_res = await client.post("/api/execution/trace", json=trace_payload)
        assert trace_res.status_code == 200
        trace_data = trace_res.json()
        assert trace_data["success"]
        assert len(trace_data["steps"]) > 0
        print(f"[API TEST 8/10] /api/execution/trace OK: Captured {len(trace_data['steps'])} line/variable event steps")

        # 9. AI Code Autopsy /api/ai/autopsy
        autopsy_payload = {
            "code": "numbers = [2, 4, 6, 8]\ntotal = 0\nfor i in range(len(numbers)):\n    total = i\nprint(total)",
            "expected_behavior": "total = 20",
            "actual_output": "3"
        }
        autopsy_res = await client.post("/api/ai/autopsy", json=autopsy_payload, headers=auth_headers)
        assert autopsy_res.status_code == 200
        autopsy_data = autopsy_res.json()
        assert "misconception_identified" in autopsy_data
        print(f"[API TEST 9/10] /api/ai/autopsy OK: Identified '{autopsy_data['misconception_identified']}'")

        # 10. Dashboard & Programming DNA /api/analytics/dashboard
        dash_res = await client.get("/api/analytics/dashboard", headers=auth_headers)
        assert dash_res.status_code == 200
        dash_data = dash_res.json()
        assert dash_data["problems_solved"] >= 1
        assert "programming_dna" in dash_data
        archetype = dash_data["programming_dna"]["overall_dna_archetype"]
        print(f"[API TEST 10/10] /api/analytics/dashboard OK: Programming DNA Archetype = '{archetype}'")

    print("=" * 60)
    print("ALL 10 API INTEGRATION TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_integration_tests())
