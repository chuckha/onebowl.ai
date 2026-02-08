import os
import sqlite3
import time

from models import BowledRecipe

_DB_PATH = os.environ.get("CACHE_DB_PATH", "cache.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS cache "
        "(url TEXT PRIMARY KEY, data TEXT NOT NULL, created_at REAL NOT NULL)"
    )
    # Migration: add flagged column if it doesn't exist yet.
    columns = {row[1] for row in conn.execute("PRAGMA table_info(cache)").fetchall()}
    if "flagged" not in columns:
        conn.execute("ALTER TABLE cache ADD COLUMN flagged INTEGER NOT NULL DEFAULT 0")
        conn.commit()
    return conn


def get(url: str) -> BowledRecipe | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT data FROM cache WHERE url = ?", (url,)
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return BowledRecipe.model_validate_json(row[0])


def put(url: str, recipe: BowledRecipe) -> None:
    conn = _connect()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO cache (url, data, created_at) VALUES (?, ?, ?)",
            (url, recipe.model_dump_json(), time.time()),
        )
        conn.commit()
    finally:
        conn.close()


def recent(limit: int = 10) -> list[BowledRecipe]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT data FROM cache ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    finally:
        conn.close()
    return [BowledRecipe.model_validate_json(row[0]) for row in rows]


def flag(url: str) -> bool:
    """Mark a recipe as flagged. Returns True if a row was updated."""
    conn = _connect()
    try:
        cursor = conn.execute(
            "UPDATE cache SET flagged = 1 WHERE url = ?", (url,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
