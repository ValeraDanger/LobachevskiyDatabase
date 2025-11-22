import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from utils.logger import setup_logging, get_logger
from utils.config import (
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
    DB_MIN_POOL_SIZE, DB_MAX_POOL_SIZE,
)

from database.async_db import AsyncDatabase
from database.managers.rbac_manager import RbacManager
from database.managers.user_manager import UserManager
from database.managers.document_manager import DocumentManager
from database.managers.workspace_manager import WorkspaceManager
from database.managers.audit_manager import AuditManager

from apps.services.auth_service import AuthService

from apps.api.routers import router as api_router

setup_logging(level=logging.DEBUG, log_to_file=True)
log = get_logger("[API]")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Подключаемся к БД...")
    db = AsyncDatabase(
        db_name=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        min_size=DB_MIN_POOL_SIZE,
        max_size=DB_MAX_POOL_SIZE,
    )
    await db.connect()
    log.info("БД подключена [✓]")

    app.state.db = db
    app.state.rbac_manager = RbacManager(db)
    app.state.user_manager = UserManager(db)
    app.state.document_manager = DocumentManager(db)
    app.state.workspace_manager = WorkspaceManager(db)
    app.state.audit_manager = AuditManager(db)

    app.state.auth_service = AuthService(app.state.user_manager, app.state.rbac_manager)

    try:
        yield
    finally:
        await db.close()
        log.info("Соединение с БД закрыто [✓]")


app = FastAPI(
    title="Platform Lobachevsky API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")