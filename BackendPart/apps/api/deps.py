from uuid import UUID
from fastapi import Depends, HTTPException, Request, status

from database.async_db import AsyncDatabase
from database.managers.user_manager import UserManager
from database.managers.document_manager import DocumentManager
from database.managers.workspace_manager import WorkspaceManager
from database.managers.rbac_manager import RbacManager
from database.managers.audit_manager import AuditManager

from apps.services.auth_service import AuthService
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from apps.core.security import decode_token


def get_db(request: Request) -> AsyncDatabase:
    return request.app.state.db


def get_user_manager(request: Request) -> UserManager:
    return request.app.state.user_manager


def get_document_manager(request: Request) -> DocumentManager:
    return request.app.state.document_manager


def get_workspace_manager(request: Request) -> WorkspaceManager:
    return request.app.state.workspace_manager


def get_rbac_manager(request: Request) -> RbacManager:
    return request.app.state.rbac_manager


def get_audit_manager(request: Request) -> AuditManager:
    return request.app.state.audit_manager


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


# ------------------ авторизация + права ------------------

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    user_manager: UserManager = Depends(get_user_manager),
):
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    token = creds.credentials
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
        )

    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    try:
        user_id = UUID(sub)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user id in token"
        )

    user = await user_manager.get_user_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return user


def require_auth():
    """
    Просто аутентификация (без проверки прав)
    """

    async def _dep(user=Depends(get_current_user)):
        return user

    return _dep


def require_permission(permission_code: str):
    """
    Проверяет наличие конкретного permission у текущего пользователя
    """

    async def _dep(
        user=Depends(get_current_user),
        rbac: RbacManager = Depends(get_rbac_manager),
    ):
        has_perm = await rbac.user_has_permission(user.id, permission_code)
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )
        return user

    return _dep
