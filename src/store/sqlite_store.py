import os
import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional
from datetime import datetime, timezone

# Simple SQLite store with per-operation connections and thread-safety.
# This module keeps a global DB path set by init_db(), and helpers operate on it.

_DB_PATH_LOCK = threading.Lock()
_DB_PATH: Optional[str] = None


def init_db(db_path: str) -> None:
    """
    Initialize the database and create required tables if they do not exist.
    """
    global _DB_PATH
    with _DB_PATH_LOCK:
        _DB_PATH = db_path

    # Ensure containing directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    with _conn() as con:
        cur = con.cursor()
        # Jobs table: store input and result as strings (JSON text)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                payment_id TEXT,
                status TEXT,
                input_json TEXT,
                result_str TEXT,
                fail_reason TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        # Cache table: one row per (address, network)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                address TEXT NOT NULL,
                network TEXT NOT NULL,
                result_json TEXT NOT NULL,
                computed_at INTEGER NOT NULL,
                PRIMARY KEY (address, network)
            )
            """
        )
        # Helpful indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_input_created ON jobs (input_json, created_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs (created_at)")
        con.commit()


@contextmanager
def _conn():
    """
    Context manager yielding a SQLite connection with sane pragmas.
    One connection per operation for simplicity/safety under FastAPI concurrency.
    """
    if _DB_PATH is None:
        raise RuntimeError("Database not initialized. Call init_db(db_path) first.")
    con = sqlite3.connect(_DB_PATH, timeout=10, check_same_thread=False)
    try:
        # Improve durability/concurrency
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        con.execute("PRAGMA foreign_keys=ON;")
        yield con
    finally:
        con.close()


def create_job(
    job_id: str,
    payment_id: str,
    status: str,
    input_json: str,
    created_at: str,
    updated_at: Optional[str] = None,
    result_str: Optional[str] = None,
    fail_reason: Optional[str] = None,
) -> None:
    """
    Insert a new job row.
    """
    with _conn() as con:
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO jobs (job_id, payment_id, status, input_json, result_str, fail_reason, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                payment_id,
                status,
                input_json,
                result_str,
                fail_reason,
                created_at,
                updated_at or created_at,
            ),
        )
        con.commit()


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a job row by id. Returns a dict or None.
    """
    with _conn() as con:
        cur = con.cursor()
        cur.execute(
            "SELECT job_id, payment_id, status, input_json, result_str, fail_reason, created_at, updated_at FROM jobs WHERE job_id = ?",
            (job_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "job_id": row[0],
            "payment_id": row[1],
            "status": row[2],
            "input_json": row[3],
            "result_str": row[4],
            "fail_reason": row[5],
            "created_at": row[6],
            "updated_at": row[7],
        }


def update_job_status(
    job_id: str,
    status: str,
    updated_at: str,
    result_str: Optional[str] = None,
    fail_reason: Optional[str] = None,
) -> None:
    """
    Update a job's status, optionally setting result and fail reason.
    """
    with _conn() as con:
        cur = con.cursor()
        if result_str is not None and fail_reason is not None:
            cur.execute(
                "UPDATE jobs SET status = ?, updated_at = ?, result_str = ?, fail_reason = ? WHERE job_id = ?",
                (status, updated_at, result_str, fail_reason, job_id),
            )
        elif result_str is not None:
            cur.execute(
                "UPDATE jobs SET status = ?, updated_at = ?, result_str = ? WHERE job_id = ?",
                (status, updated_at, result_str, job_id),
            )
        elif fail_reason is not None:
            cur.execute(
                "UPDATE jobs SET status = ?, updated_at = ?, fail_reason = ? WHERE job_id = ?",
                (status, updated_at, fail_reason, job_id),
            )
        else:
            cur.execute(
                "UPDATE jobs SET status = ?, updated_at = ? WHERE job_id = ?",
                (status, updated_at, job_id),
            )
        con.commit()


def get_cache(address: str, network: str, max_age_sec: int) -> Optional[str]:
    """
    Return result_json from cache if present and not older than max_age_sec, else None.
    """
    now = int(time.time())
    threshold = now - max_age_sec
    with _conn() as con:
        cur = con.cursor()
        cur.execute(
            "SELECT result_json, computed_at FROM cache WHERE address = ? AND network = ?",
            (address, network),
        )
        row = cur.fetchone()
        if not row:
            return None
        result_json, computed_at = row[0], int(row[1])
        if computed_at >= threshold:
            return result_json
        return None


def upsert_cache(address: str, network: str, result_json: str, computed_at: Optional[int] = None) -> None:
    """
    Insert or update the cache entry for (address, network).
    """
    ts = int(computed_at or time.time())
    with _conn() as con:
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO cache (address, network, result_json, computed_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(address, network) DO UPDATE SET
                result_json = excluded.result_json,
                computed_at = excluded.computed_at
            """,
            (address, network, result_json, ts),
        )
        con.commit()

def find_recent_job_by_input(input_json: str, within_seconds: int) -> Optional[Dict[str, Any]]:
    """
    Return the most recent job for the exact input_json if it was created within 'within_seconds'.
    Used for idempotency (dedupe).
    """
    with _conn() as con:
        cur = con.cursor()
        cur.execute(
            "SELECT job_id, payment_id, status, input_json, result_str, fail_reason, created_at, updated_at FROM jobs WHERE input_json = ? ORDER BY created_at DESC LIMIT 1",
            (input_json,),
        )
        row = cur.fetchone()
        if not row:
            return None
        rec = {
            "job_id": row[0],
            "payment_id": row[1],
            "status": row[2],
            "input_json": row[3],
            "result_str": row[4],
            "fail_reason": row[5],
            "created_at": row[6],
            "updated_at": row[7],
        }
        try:
            dt = datetime.strptime(rec["created_at"], "%Y-%m-%d %H:%M:%S %Z")
            if dt.tzinfo is None:
                created_ts = int(dt.replace(tzinfo=timezone.utc).timestamp())
            else:
                created_ts = int(dt.timestamp())
        except Exception:
            return None
        now_ts = int(time.time())
        if now_ts - created_ts <= within_seconds:
            return rec
        return None
