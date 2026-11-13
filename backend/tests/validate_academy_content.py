"""
Content validator for the Coding Academy seed data (no database needed).

- Every C reference solution must pass all of its own test cases on Judge0.
- Every SQL reference answer must run in the sandbox and match itself.
- Every quiz answer index must point at an existing option.
- Starter code must NOT already pass (otherwise the task is free XP).

Run:  .venv\\Scripts\\python.exe backend\\tests\\validate_academy_content.py
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.academy.content import COURSES, SQL_DATASET
from app.academy.grading import grade_code_task, grade_sql_task, grade_quiz


def task_row(task):
    return {
        "test_cases": json.dumps(task.get("tests", [])),
        "setup_sql": SQL_DATASET,
        "reference_sql": task.get("reference_sql"),
        "check_sql": task.get("check_sql"),
        "order_matters": task.get("order_matters", False),
        "questions": json.dumps(task.get("questions", [])),
        "pass_mark": task.get("pass_mark", 70),
        "concept": "x",
    }


async def main():
    failures = []
    counts = {"code": 0, "sql": 0, "quiz": 0}
    for course in COURSES:
        for level in course["levels"]:
            tasks = [lesson["task"] for lesson in level["lessons"]] + [dict(level["assessment"], type="quiz")]
            for task in tasks:
                row = task_row(task)
                kind = task["type"]
                counts[kind] += 1
                if kind == "code":
                    good = await grade_code_task(row, task["solution"])
                    if not good["passed"]:
                        failures.append(f"{task['id']}: reference solution failed -> {good['status']} {good['test_results']} {good['error']}")
                    starter = await grade_code_task(row, task["starter"])
                    if starter["passed"]:
                        failures.append(f"{task['id']}: starter code already passes")
                elif kind == "sql":
                    good = grade_sql_task(row, task["reference_sql"])
                    if not good["passed"]:
                        failures.append(f"{task['id']}: reference SQL failed -> {good['error']} {good['details']}")
                    rows = good["details"]["student"].get("rows", []) if good.get("details") else []
                    if not rows:
                        failures.append(f"{task['id']}: reference result is empty (task cannot distinguish answers)")
                    starter = grade_sql_task(row, task.get("starter") or "")
                    if starter["passed"]:
                        failures.append(f"{task['id']}: starter SQL already passes")
                else:
                    qs = task["questions"]
                    for i, item in enumerate(qs):
                        if not (0 <= item["answer"] < len(item["options"])):
                            failures.append(f"{task['id']} q{i}: answer index out of range")
                    if not grade_quiz(row, [item["answer"] for item in qs])["passed"]:
                        failures.append(f"{task['id']}: answer key does not pass its own pass mark")
                    if grade_quiz(row, [])["passed"]:
                        failures.append(f"{task['id']}: empty answers pass")
                print(f"  checked {task['id']:<22} ({kind})")

    print(f"\nChecked {counts['code']} C tasks, {counts['sql']} SQL tasks, {counts['quiz']} quizzes.")
    if failures:
        print(f"{len(failures)} FAILURE(S):")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("ALL ACADEMY CONTENT VALID.")


if __name__ == "__main__":
    asyncio.run(main())
