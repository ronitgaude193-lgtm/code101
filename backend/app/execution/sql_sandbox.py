"""
SQL exercise sandbox: runs student SQL in an isolated child process against a
fresh in-memory copy of the exercise dataset, then compares the result with the
task's reference answer.
"""
import json
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional

SQL_WORKER_PATH = os.path.join(os.path.dirname(__file__), "sql_worker.py")
SQL_TIMEOUT_SECONDS = 4.0


def run_sql(setup_sql: str, student_sql: str, check_sql: Optional[str] = None) -> Dict[str, Any]:
    if not (student_sql or "").strip():
        return {"ok": False, "stage": "student", "error": "Write a SQL statement first."}

    fd, payload_path = tempfile.mkstemp(suffix=".json", prefix="sqltask_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"setup_sql": setup_sql, "student_sql": student_sql, "check_sql": check_sql}, f)
        proc = subprocess.run(
            [sys.executable, "-I", SQL_WORKER_PATH, payload_path],
            capture_output=True,
            text=True,
            timeout=SQL_TIMEOUT_SECONDS,
        )
        out = (proc.stdout or "").strip().splitlines()
        if not out:
            return {"ok": False, "stage": "worker", "error": (proc.stderr or "SQL worker produced no output").strip()[-500:]}
        return json.loads(out[-1])
    except subprocess.TimeoutExpired:
        return {"ok": False, "stage": "student", "error": f"Query timed out after {SQL_TIMEOUT_SECONDS:.0f} seconds."}
    finally:
        try:
            os.remove(payload_path)
        except OSError:
            pass


def _norm_value(v: Any) -> Any:
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, float):
        r = round(v, 2)
        return int(r) if r.is_integer() else r
    if isinstance(v, str):
        s = v.strip()
        try:
            f = float(s)
            r = round(f, 2)
            return int(r) if r.is_integer() else r
        except ValueError:
            return s
    return v


def normalize_rows(rows: List[List[Any]]) -> List[tuple]:
    return [tuple(_norm_value(v) for v in row) for row in rows]


def compare_results(student: Dict[str, Any], expected: Dict[str, Any], order_matters: bool) -> Dict[str, Any]:
    """
    Compares two successful run_sql results. Column names are ignored (aliases are
    allowed); column count, values and (when required) row order must match.
    """
    s_rows = normalize_rows(student.get("rows", []))
    e_rows = normalize_rows(expected.get("rows", []))
    s_cols = len(student.get("columns", []))
    e_cols = len(expected.get("columns", []))

    if s_cols != e_cols:
        return {"passed": False, "reason": "wrong-columns",
                "detail": f"Your result has {s_cols} column(s); the expected result has {e_cols}."}

    key = lambda r: tuple((str(type(v)), str(v)) for v in r)
    same_set = sorted(s_rows, key=key) == sorted(e_rows, key=key)

    if order_matters:
        if s_rows == e_rows:
            return {"passed": True, "reason": None, "detail": "Result matches the expected rows and order."}
        if same_set:
            return {"passed": False, "reason": "ordering",
                    "detail": "You returned the right rows, but in the wrong order."}
    elif same_set:
        return {"passed": True, "reason": None, "detail": "Result matches the expected rows."}

    if len(s_rows) > len(e_rows):
        return {"passed": False, "reason": "too-many-rows",
                "detail": f"Your query returned {len(s_rows)} row(s); the expected result has {len(e_rows)}."}
    if len(s_rows) < len(e_rows):
        return {"passed": False, "reason": "too-few-rows",
                "detail": f"Your query returned {len(s_rows)} row(s); the expected result has {len(e_rows)}."}
    return {"passed": False, "reason": "wrong-values",
            "detail": "Same number of rows as expected, but some values differ."}
