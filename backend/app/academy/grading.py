"""
Deterministic verification for Coding Academy tasks.

- code: C programs compiled and run by Judge0 against stdin/stdout test cases
- sql:  student SQL run in the isolated SQL sandbox and compared with the reference query
- quiz: answers compared with the stored answer key

The LLM is never involved in deciding whether a task passed.
"""
import json
from typing import Any, Dict, List, Optional

from app.execution.judge0_client import judge0_client
from app.execution.sql_sandbox import run_sql, compare_results


def _normalize_output(text: str) -> str:
    lines = (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return "\n".join(line.rstrip() for line in lines).strip("\n")


async def run_c_program(code: str, stdin: str = "") -> Dict[str, Any]:
    if not judge0_client.is_configured():
        return {
            "success": False, "stdout": "", "stderr": "",
            "compile_output": "C tasks are compiled by Judge0. Set JUDGE0_API_URL in backend/.env (e.g. https://ce.judge0.com).",
            "exit_code": -1, "execution_time": 0.0, "status": "Judge0 Not Configured",
        }
    return await judge0_client.execute(code, "c", stdin)


async def grade_code_task(task: Dict[str, Any], code: str) -> Dict[str, Any]:
    tests = json.loads(task["test_cases"] or "[]")
    results: List[Dict[str, Any]] = []
    total_time = 0.0
    first_error: Optional[str] = None
    status_detail: Optional[str] = None

    for idx, tc in enumerate(tests, start=1):
        res = await run_c_program(code, tc.get("stdin", ""))
        total_time += float(res.get("execution_time") or 0.0)
        compile_output = (res.get("compile_output") or "").strip()
        stderr = (res.get("stderr") or "").strip()
        status = res.get("status", "")
        actual = _normalize_output(res.get("stdout") or "")
        expected = _normalize_output(tc.get("expected_output", ""))

        passed = bool(res.get("success")) and actual == expected
        if not passed and first_error is None and (compile_output or stderr or status not in ("Accepted", "")):
            first_error = compile_output or stderr or status
            status_detail = status
        hidden = bool(tc.get("hidden"))
        results.append({
            "case_index": idx,
            "input": "[Hidden Test Case]" if hidden else tc.get("stdin", ""),
            "expected_output": "[Hidden]" if hidden else expected,
            "actual_output": ("[Passed]" if passed else actual) if hidden else actual,
            "passed": passed,
            "hidden": hidden,
        })
        # A compile error fails every case identically - stop early.
        if compile_output and "Compilation Error" in status:
            for j, rest in enumerate(tests[idx:], start=idx + 1):
                results.append({
                    "case_index": j,
                    "input": "[Hidden Test Case]" if rest.get("hidden") else rest.get("stdin", ""),
                    "expected_output": "[Hidden]" if rest.get("hidden") else _normalize_output(rest.get("expected_output", "")),
                    "actual_output": "", "passed": False, "hidden": bool(rest.get("hidden")),
                })
            break

    passed_count = sum(1 for r in results if r["passed"])
    all_passed = passed_count == len(tests) and len(tests) > 0
    if all_passed:
        status_label = "Accepted"
    elif status_detail and "Compilation" in status_detail:
        status_label = "Compilation Error"
    elif status_detail and status_detail != "Accepted":
        status_label = status_detail
    else:
        status_label = "Wrong Answer"

    return {
        "passed": all_passed,
        "status": status_label,
        "passed_count": passed_count,
        "total_count": len(tests),
        "test_results": results,
        "error": first_error,
        "execution_seconds": round(total_time, 3),
        "details": None,
    }


def run_sql_task(task: Dict[str, Any], student_sql: str) -> Dict[str, Any]:
    """Runs (without grading) for the 'Run' button: shows the student's result table."""
    return run_sql(task["setup_sql"] or "", student_sql, task.get("check_sql"))


def grade_sql_task(task: Dict[str, Any], student_sql: str) -> Dict[str, Any]:
    student = run_sql(task["setup_sql"] or "", student_sql, task.get("check_sql"))
    if not student.get("ok"):
        return {
            "passed": False, "status": "SQL Error", "passed_count": 0, "total_count": 1,
            "test_results": [], "error": student.get("error"), "execution_seconds": 0.0,
            "details": {"student": student, "comparison": None},
        }
    expected = run_sql(task["setup_sql"] or "", task["reference_sql"], task.get("check_sql"))
    if not expected.get("ok"):
        # Content error, not the student's fault.
        return {
            "passed": False, "status": "Task Configuration Error", "passed_count": 0, "total_count": 1,
            "test_results": [], "error": f"Reference answer failed: {expected.get('error')}",
            "execution_seconds": 0.0, "details": {"student": student, "comparison": None},
        }
    comparison = compare_results(student, expected, bool(task.get("order_matters")))
    return {
        "passed": comparison["passed"],
        "status": "Accepted" if comparison["passed"] else "Wrong Result",
        "passed_count": 1 if comparison["passed"] else 0,
        "total_count": 1,
        "test_results": [],
        "error": None,
        "execution_seconds": 0.0,
        "details": {
            "student": student,
            "comparison": comparison,
            "expected_row_count": len(expected.get("rows", [])),
            "expected_column_count": len(expected.get("columns", [])),
        },
    }


def public_questions(task: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Quiz questions without the answer key."""
    return [
        {"index": i, "question": item["q"], "options": item["options"], "concept": item.get("concept")}
        for i, item in enumerate(json.loads(task["questions"] or "[]"))
    ]


def grade_quiz(task: Dict[str, Any], answers: List[int]) -> Dict[str, Any]:
    questions = json.loads(task["questions"] or "[]")
    feedback = []
    correct = 0
    weak_concepts: List[str] = []
    strong_concepts: List[str] = []
    for i, item in enumerate(questions):
        chosen = answers[i] if i < len(answers) else None
        ok = chosen == item["answer"]
        correct += 1 if ok else 0
        concept = item.get("concept") or task.get("concept")
        (strong_concepts if ok else weak_concepts).append(concept)
        feedback.append({
            "index": i,
            "correct": ok,
            "chosen": chosen,
            "correct_option": item["answer"],
            "explanation": item.get("explain", ""),
            "concept": concept,
        })
    total = len(questions)
    score = round(100.0 * correct / total, 1) if total else 0.0
    passed = total > 0 and score >= float(task.get("pass_mark") or 70)
    return {
        "passed": passed,
        "status": "Passed" if passed else "Not Passed",
        "passed_count": correct,
        "total_count": total,
        "test_results": [],
        "error": None,
        "execution_seconds": 0.0,
        "score": score,
        "details": {
            "questions": feedback,
            "weak_concepts": sorted(set(weak_concepts)),
            "strong_concepts": sorted(set(strong_concepts)),
        },
    }
