from typing import Any, List, Optional

import asyncpg
from asyncpg.pool import Pool

from utils.logger import get_logger

log = get_logger(__name__)


class AsyncDatabase:
    def __init__(
            self,
            db_name: str,
            user: str,
            password: str,
            host: str = "localhost",
            port: int = 5432,
            min_size: int = 10,
            max_size: int = 100
    ):
        self.db_name = db_name
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[Pool] = None

    async def connect(self) -> None:
        try:
            self.pool = await asyncpg.create_pool(
                database=self.db_name,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                min_size=self.min_size,
                max_size=self.max_size
            )
            log.debug("[DB] Подключение к базе данных успешно установлено")
        except Exception as e:
            log.exception(f"[DB] Ошибка при подключении к базе данных: {e}")

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()
            log.debug("[DB] Соединение с базой данных закрыто.")

    async def execute(self, query: str, *args: Any) -> str:
        if not self.pool:
            raise RuntimeError("Database pool is not initialized. Did you forget to call connect()?")

        async with self.pool.acquire() as connection:
            async with connection.transaction():
                return await connection.execute(query, *args)

    async def fetch(self, query: str, *args: Any) -> List[asyncpg.Record]:
        if not self.pool:
            raise RuntimeError("Database pool is not initialized. Did you forget to call connect()?")
        
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                return await connection.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> Optional[asyncpg.Record]:
        if not self.pool:
            raise RuntimeError("Database pool is not initialized. Did you forget to call connect()?")
        
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                return await connection.fetchrow(query, *args)

    async def fetchval(self, query: str, *args: Any, column: int = 0) -> Any:
        if not self.pool:
            raise RuntimeError("Database pool is not initialized. Did you forget to call connect()?")
        
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                return await connection.fetchval(query, *args, column=column)