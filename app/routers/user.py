
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import get_password_hash, verify_password
from app.database import get_db
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.user import (
    ChangePasswordRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.user_service import UserService
from fastapi import Request

from app.repositories.user_repository import UserRepository
from app.services.audit_log_service import AuditLogService


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    try:
        return UserService.register_user(db, user_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post("/login", response_model=TokenResponse)
def login_user(
    user_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    email = str(user_data.email).lower()

    user = UserRepository.get_by_email(db, email)

    try:
        result = UserService.login_user(
            db=db,
            email=email,
            password=user_data.password,
        )

        AuditLogService.create_log(
            db=db,
            user_id=user.id if user else None,
            action="LOGIN",
            entity="USER",
            entity_id=user.id if user else None,
            request=request,
            metadata={"result": "SUCCESS"},
        )

        db.commit()

        return result

    except ValueError as exc:
        AuditLogService.create_log(
            db=db,
            user_id=user.id if user else None,
            action="FAILED_LOGIN",
            entity="USER",
            entity_id=user.id if user else None,
            request=request,
            metadata={"reason": str(exc)},
        )

        db.commit()

        if str(exc) == "Invalid email or password":
            code = status.HTTP_401_UNAUTHORIZED
        else:
            code = status.HTTP_403_FORBIDDEN

        raise HTTPException(
            status_code=code,
            detail=str(exc),
        ) from exc

@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user

@router.post("/refresh")
def refresh_access_token(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    try:
        return UserService.refresh_access_token(
            db=db,
            refresh_token=token_data.refresh_token,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
        
@router.post("/logout")
def logout_user(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    try:
        return UserService.logout_user(
            db=db,
            refresh_token=token_data.refresh_token,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
        

@router.post("/change-password")
def change_password(
    password_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return UserService.change_password(
            db=db,
            user=current_user,
            current_password=password_data.current_password,
            new_password=password_data.new_password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc