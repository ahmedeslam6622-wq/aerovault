"""Auth router — login (all users), superuser TOTP verification."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from database import get_db
from models.user import User, UserRole
from auth.security import verify_password, create_access_token, verify_totp
from auth.dependencies import get_current_user

router = APIRouter()


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    full_name: str
    role: str
    notification_mode: str
    requires_totp: bool = False


class TOTPRequest(BaseModel):
    username: str
    password: str
    totp_code: str


@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()

    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled.")

    # Superuser requires TOTP — signal frontend to ask for code
    if user.role == UserRole.SUPERUSER:
        return {"requires_totp": True, "username": user.username}

    # All other roles: issue token immediately
    token = create_access_token({"sub": user.username, "role": user.role})
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    return LoginResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        role=user.role.value,
        notification_mode=user.notification_mode.value,
    )


@router.post("/login/superuser")
async def login_superuser(req: TOTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.username == req.username,
        User.role == UserRole.SUPERUSER,
    ).first()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    if not user.totp_secret or not verify_totp(user.totp_secret, req.totp_code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authenticator code. Codes refresh every 30 seconds.",
        )

    token = create_access_token({"sub": user.username, "role": user.role}, expires_minutes=60*4)  # 4h for superuser
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    return LoginResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        role=user.role.value,
        notification_mode=user.notification_mode.value,
    )


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "department": current_user.department,
        "employee_id": current_user.employee_id,
        "role": current_user.role.value,
        "notification_mode": current_user.notification_mode.value,
        "avatar_initials": current_user.avatar_initials,
        "is_active": current_user.is_active,
        "last_login": current_user.last_login,
    }


@router.post("/logout")
async def logout():
    # JWT is stateless — client discards token
    return {"message": "Logged out successfully."}
