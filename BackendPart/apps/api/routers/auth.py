from fastapi import APIRouter, Depends, HTTPException
from apps.api.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    LogoutRequest,
    TokenPair,
)
from apps.services.auth_service import AuthService
from apps.api.deps import get_auth_service, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair)
async def register(
    data: RegisterRequest,
    auth: AuthService = Depends(get_auth_service),
):
    if data.password != data.password_confirm:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    try:
        access, refresh = await auth.register(
            first_name=data.first_name,
            last_name=data.last_name,
            middle_name=data.middle_name,
            department_id=data.department_id,
            phone=data.phone,
            email=data.email,
            password=data.password,
        )
    except ValueError as e:
        if str(e) == "email_taken":
            raise HTTPException(status_code=400, detail="User already exists")
        raise

    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenPair)
async def login(data: LoginRequest, auth: AuthService = Depends(get_auth_service)):
    result = await auth.login(data.email, data.password)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access, refresh = result
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/logout")
async def logout(
    data: LogoutRequest,
    auth: AuthService = Depends(get_auth_service),
    user=Depends(get_current_user),
):
    await auth.logout(data.refresh_token)
    return {"detail": "Logged out"}
