import json
import time
import aiosqlite
from typing import Any, Optional


class Database:
    def __init__(self, db_path: str = "cache.db"):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def init(self):
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS company_cache (
                credit_code  TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                created_at   INTEGER NOT NULL,
                expires_at   INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS module_data (
                credit_code  TEXT NOT NULL,
                module       TEXT NOT NULL,
                status       TEXT NOT NULL,
                data_json    TEXT,
                error_msg    TEXT,
                updated_at   INTEGER NOT NULL,
                PRIMARY KEY (credit_code, module)
            );
            CREATE TABLE IF NOT EXISTS tasks (
                task_id     TEXT PRIMARY KEY,
                credit_code TEXT NOT NULL,
                created_at  INTEGER NOT NULL,
                status      TEXT NOT NULL
            );
        """)
        await self._conn.commit()

    async def close(self):
        if self._conn:
            await self._conn.close()

    async def upsert_company(self, credit_code: str, company_name: str, ttl_seconds: int = 86400):
        now = int(time.time())
        await self._conn.execute(
            "INSERT OR REPLACE INTO company_cache VALUES (?, ?, ?, ?)",
            (credit_code, company_name, now, now + ttl_seconds),
        )
        await self._conn.commit()

    async def is_company_cached(self, credit_code: str) -> bool:
        now = int(time.time())
        async with self._conn.execute(
            "SELECT 1 FROM company_cache WHERE credit_code = ? AND expires_at > ?",
            (credit_code, now),
        ) as cur:
            return await cur.fetchone() is not None

    async def save_module_data(
        self, credit_code: str, module: str, status: str,
        data: Optional[Any] = None, error_msg: Optional[str] = None
    ):
        await self._conn.execute(
            """INSERT OR REPLACE INTO module_data
               (credit_code, module, status, data_json, error_msg, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (credit_code, module, status,
             json.dumps(data, ensure_ascii=False) if data is not None else None,
             error_msg, int(time.time())),
        )
        await self._conn.commit()

    async def get_module_data(self, credit_code: str, module: str) -> Optional[dict]:
        async with self._conn.execute(
            "SELECT status, data_json, error_msg FROM module_data WHERE credit_code = ? AND module = ?",
            (credit_code, module),
        ) as cur:
            row = await cur.fetchone()
        if row is None:
            return None
        return {
            "status": row["status"],
            "data": json.loads(row["data_json"]) if row["data_json"] else None,
            "error": row["error_msg"],
        }

    async def get_all_modules(self, credit_code: str) -> dict:
        async with self._conn.execute(
            "SELECT module, status, data_json, error_msg FROM module_data WHERE credit_code = ?",
            (credit_code,),
        ) as cur:
            rows = await cur.fetchall()
        return {
            row["module"]: {
                "status": row["status"],
                "data": json.loads(row["data_json"]) if row["data_json"] else None,
                "error": row["error_msg"],
            }
            for row in rows
        }

    async def create_task(self, task_id: str, credit_code: str):
        await self._conn.execute(
            "INSERT INTO tasks VALUES (?, ?, ?, ?)",
            (task_id, credit_code, int(time.time()), "pending"),
        )
        await self._conn.commit()

    async def get_task(self, task_id: str) -> Optional[dict]:
        async with self._conn.execute(
            "SELECT task_id, credit_code, status FROM tasks WHERE task_id = ?",
            (task_id,),
        ) as cur:
            row = await cur.fetchone()
        if row is None:
            return None
        return dict(row)

    async def update_task_status(self, task_id: str, status: str):
        await self._conn.execute(
            "UPDATE tasks SET status = ? WHERE task_id = ?",
            (status, task_id),
        )
        await self._conn.commit()
