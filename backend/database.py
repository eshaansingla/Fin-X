import os
import sqlite3

from dotenv import load_dotenv

load_dotenv(override=True)

DB_PATH = os.getenv("DATABASE_URL", "data/falcon.db")


def get_conn():
    """
    Returns a SQLite connection with:
    - row_factory=sqlite3.Row so rows behave like dicts
    - WAL mode enabled for concurrent reads/writes (APScheduler + FastAPI run simultaneously)
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """
    Idempotent schema creation. Safe to call multiple times.
    Called once at FastAPI startup via the @app.on_event('startup') hook.
    """
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS bulk_deals (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol      TEXT NOT NULL,
            client_name TEXT,
            deal_type   TEXT,
            quantity    INTEGER,
            price       REAL,
            deal_date   TEXT,
            fetched_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS signals (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id         INTEGER,
            symbol          TEXT NOT NULL,
            explanation     TEXT,
            signal_type     TEXT,
            risk_level      TEXT,
            confidence      INTEGER,
            key_observation TEXT,
            disclaimer      TEXT,
            created_at      TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (deal_id) REFERENCES bulk_deals(id)
        );

        CREATE TABLE IF NOT EXISTS news_cache (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol       TEXT,
            headline     TEXT,
            source       TEXT,
            url          TEXT,
            published_at TEXT,
            fetched_at   TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS card_cache (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol     TEXT UNIQUE,
            card_json  TEXT,
            expires_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS chat_sessions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role       TEXT NOT NULL,
            content    TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_signals_symbol  ON signals(symbol);
        CREATE INDEX IF NOT EXISTS idx_signals_created ON signals(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_chat_session    ON chat_sessions(session_id);
        CREATE INDEX IF NOT EXISTS idx_deals_symbol    ON bulk_deals(symbol);
    """
    )

    # Migrate existing DB: add key_observation if missing
    try:
        cur.execute('ALTER TABLE signals ADD COLUMN key_observation TEXT')
        print('[DB] Migrated: added key_observation column')
    except Exception:
        pass  # Column already exists — safe to ignore

    conn.commit()
    conn.close()
    print("[DB] Initialized successfully")


def db_fetchall(query: str, params: tuple = ()) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def db_fetchone(query: str, params: tuple = ()) -> dict | None:
    conn = get_conn()
    row = conn.execute(query, params).fetchone()
    conn.close()
    return dict(row) if row else None


def db_execute(query: str, params: tuple = ()) -> int:
    conn = get_conn()
    cur = conn.execute(query, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id
