"""FastAPI auth dependencies — inject current user, enforce roles."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from models.user import User, UserRole
from auth.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session expired or invalid. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    username: str = payload.get("sub")
    if not username:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise credentials_exception
    return user


def require_roles(*roles: UserRole):
    """Factory: returns a dependency that allows only the specified roles."""
    def _check(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {' or '.join(r.value for r in roles)}.",
            )
        return current_user
    return _check


# Convenience dependencies
require_viewer_plus       = require_roles(*UserRole)  # Any authenticated user
require_flight_manager    = require_roles(UserRole.FLIGHT_MANAGER, UserRole.ADMIN, UserRole.SUPERUSER)
require_maintenance_chief = require_roles(UserRole.MAINT_CHIEF, UserRole.ADMIN, UserRole.SUPERUSER)
require_admin             = require_roles(UserRole.ADMIN, UserRole.SUPERUSER)
require_superuser         = require_roles(UserRole.SUPERUSER)
