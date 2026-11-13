"""
PostgreSQL (Supabase) connection layer.

`get_db()` yields a psycopg connection whose cursors return dict rows, so
callers can keep using `row["column"]`. The transaction is committed when the
block exits normally and rolled back on any exception.
"""
import atexit
import os
import sys
import glob
from contextlib import contextmanager
from typing import Generator, Optional

# Windows Smart App Control & libpq resolution helper
if sys.platform == "win32":
    libs_dir = os.path.join(sys.prefix, "Lib", "site-packages", "psycopg2_binary.libs")
    if os.path.exists(libs_dir):
        libpq_dll = os.path.join(libs_dir, "libpq.dll")
        if not os.path.exists(libpq_dll):
            matches = glob.glob(os.path.join(libs_dir, "libpq*.dll"))
            if matches:
                import shutil
                shutil.copyfile(matches[0], libpq_dll)
        if libs_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = libs_dir + os.pathsep + os.environ.get("PATH", "")
        os.environ.setdefault("PSYCOPG_IMPL", "python")

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.core.config import settings

SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.sql")

_pool: Optional[ConnectionPool] = None


def _get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        if not settings.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is not set. Add your Supabase Postgres connection string "
                "to backend/.env (Supabase Dashboard -> Connect -> Connection string)."
            )
        _pool = ConnectionPool(
            conninfo=settings.DATABASE_URL,
            min_size=1,
            max_size=10,
            # prepare_threshold=None disables server-side prepared statements,
            # which Supabase's transaction pooler (port 6543) does not support.
            kwargs={"row_factory": dict_row, "prepare_threshold": None},
            # Validate connections on checkout so a connection dropped by the network
            # or the Supabase pooler is replaced instead of failing the request.
            check=ConnectionPool.check_connection,
            open=True,
        )
    return _pool


@contextmanager
def get_db() -> Generator[psycopg.Connection, None, None]:
    with _get_pool().connection() as conn:
        # The pool commits on clean exit and rolls back if an exception escapes.
        yield conn


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


atexit.register(close_pool)


def init_database() -> None:
    """Creates tables, indexes, RLS settings and seed data (idempotent)."""
    with open(SCHEMA_FILE, encoding="utf-8") as f:
        schema_sql = f.read()
    with get_db() as conn:
        # Serialise concurrent initialisers (run_app.py + app startup, multiple workers).
        conn.execute("SELECT pg_advisory_xact_lock(724001);")
        # No parameters are passed, so psycopg sends the whole script at once.
        conn.execute(schema_sql)
        # Coding Academy curriculum (idempotent upsert of course content only)
        from app.academy.content import seed_academy
        seed_academy(conn)
