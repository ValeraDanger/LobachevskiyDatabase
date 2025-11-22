from database.async_db import AsyncDatabase


class BaseManager:
    def __init__(self, db: AsyncDatabase) -> None:
        self.db = db
