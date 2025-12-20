from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Sequence

import asyncpg


@dataclass
class PgPool:
    dsn: str
    pool: Optional[asyncpg.Pool] = None

    async def init(self) -> None:
        if self.pool is None:
            self.pool = await asyncpg.create_pool(dsn=self.dsn, min_size=1, max_size=5)

    async def fetch(self, query: str, *args: Any) -> Sequence[asyncpg.Record]:
        if self.pool is None:
            raise RuntimeError("DB pool not initialized")
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> Optional[asyncpg.Record]:
        if self.pool is None:
            raise RuntimeError("DB pool not initialized")
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def execute(self, query: str, *args: Any) -> str:
        if self.pool is None:
            raise RuntimeError("DB pool not initialized")
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)


