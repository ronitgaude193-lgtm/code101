"""
Isolated SQL exercise worker (run as a separate process by sql_sandbox.py).

Reads a JSON payload file: {"setup_sql", "student_sql", "check_sql"}.
Creates a throwaway in-memory SQLite database, loads the exercise dataset,
runs the student's SQL and prints a JSON result to stdout.

This database exists only for the lifetime of this process. It never touches
the application's Supabase database.
"""
import json
import sqlite3
import sys

MAX_ROWS = 200
MAX_VM_STEPS = 2_000_000  # aborts runaway queries such as huge cross joins

DENIED_ACTIONS = {
    sqlite3.SQLITE_ATTACH,
    sqlite3.SQLITE_DETACH,
    sqlite3.SQLITE_PRAGMA,
}


def _authorizer(action, arg1, arg2, dbname, source):
    if action in DENIED_ACTIONS:
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def _fetch(cursor):
    columns = [d[0] for d in cursor.description] if cursor.description else []
    rows = cursor.fetchmany(MAX_ROWS + 1)
    truncated = len(rows) > MAX_ROWS
    return columns, [list(r) for r in rows[:MAX_ROWS]], truncated


def main():
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        payload = json.load(f)

    setup_sql = payload.get("setup_sql") or ""
    student_sql = (payload.get("student_sql") or "").strip()
    check_sql = payload.get("check_sql")

    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(setup_sql)
        conn.commit()
    except Exception as exc:
        print(json.dumps({"ok": False, "stage": "setup", "error": f"Exercise setup failed: {exc}"}))
        return

    steps = {"n": 0}

    def progress():
        steps["n"] += 1
        return 1 if steps["n"] * 1000 > MAX_VM_STEPS else 0

    conn.set_authorizer(_authorizer)
    conn.set_progress_handler(progress, 1000)

    try:
        if check_sql:
            # Data-changing / DDL task: run the student's statements, then inspect the result.
            conn.executescript(student_sql)
            conn.set_authorizer(None)
            cur = conn.execute(check_sql)
        else:
            # Query task: exactly one statement.
            cur = conn.execute(student_sql.rstrip().rstrip(";"))
        columns, rows, truncated = _fetch(cur)
        print(json.dumps({"ok": True, "columns": columns, "rows": rows, "truncated": truncated}, default=str))
    except sqlite3.OperationalError as exc:
        msg = str(exc)
        if msg == "interrupted":
            msg = "Query aborted: it did too much work (check for a missing JOIN condition)."
        elif "not authorized" in msg:
            msg = "That statement is not allowed in the SQL practice sandbox (ATTACH, DETACH and PRAGMA are blocked)."
        print(json.dumps({"ok": False, "stage": "student", "error": msg}))
    except Exception as exc:
        print(json.dumps({"ok": False, "stage": "student", "error": str(exc)}))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
