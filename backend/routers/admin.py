"""Admin router — user management (Admin and Superuser only)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from database import get_db
from models.user import User, UserRole, NotificationMode
from auth.security import hash_password
from auth.dependencies import get_current_user, require_admin

router = APIRouter()


def user_to_dict(u: User) -> dict:
    return {
        "id":               u.id,
        "username":         u.username,
        "full_name":        u.full_name,
        "email":            u.email,
        "department":       u.department,
        "employee_id":      u.employee_id,
        "role":             u.role.value,
        "notification_mode":u.notification_mode.value,
        "is_active":        u.is_active,
        "avatar_initials":  u.avatar_initials,
        "created_at":       u.created_at.isoformat() if u.created_at else None,
        "last_login":       u.last_login.isoformat()  if u.last_login  else None,
    }


@router.get("/users")
async def list_users(
    db:   Session = Depends(get_db),
    _u:   User    = Depends(require_admin),
):
    users = db.query(User).order_by(User.role, User.full_name).all()
    return {"total": len(users), "users": [user_to_dict(u) for u in users]}


class RoleUpdate(BaseModel):
    role: str


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    body:    RoleUpdate,
    db:      Session = Depends(get_db),
    actor:   User    = Depends(require_admin),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found.")
    # Only superuser can assign/change superuser role
    if body.role == UserRole.SUPERUSER and actor.role != UserRole.SUPERUSER:
        raise HTTPException(status_code=403, detail="Only a superuser can assign the superuser role.")
    try:
        u.role = UserRole(body.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {body.role}")
    db.commit()
    return {"message": f"Role updated to {body.role} for {u.full_name}."}


@router.patch("/users/{user_id}/toggle")
async def toggle_user_active(
    user_id: int,
    db:      Session = Depends(get_db),
    actor:   User    = Depends(require_admin),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found.")
    if u.role == UserRole.SUPERUSER and actor.role != UserRole.SUPERUSER:
        raise HTTPException(status_code=403, detail="Cannot disable superuser accounts.")
    if u.id == actor.id:
        raise HTTPException(status_code=400, detail="Cannot disable your own account.")
    u.is_active = not u.is_active
    db.commit()
    return {"message": f"{'Enabled' if u.is_active else 'Disabled'} account for {u.full_name}.", "is_active": u.is_active}


@router.get("/stats/summary")
async def system_stats(
    db:  Session = Depends(get_db),
    _u:  User    = Depends(require_admin),
):
    from sqlalchemy import func
    from models import Flight, CrewMember, Aircraft, MaintenanceLog
    from models.maintenance import Priority

    return {
        "total_users":    db.query(func.count(User.id)).scalar(),
        "active_users":   db.query(func.count(User.id)).filter(User.is_active == True).scalar(),
        "total_flights":  db.query(func.count(Flight.id)).scalar(),
        "total_crew":     db.query(func.count(CrewMember.id)).scalar(),
        "total_aircraft": db.query(func.count(Aircraft.id)).scalar(),
        "aog_aircraft":   db.query(func.count(Aircraft.id)).filter(Aircraft.is_aog == True).scalar(),
        "aog_tasks":      db.query(func.count(MaintenanceLog.id)).filter(MaintenanceLog.priority == Priority.AOG).scalar(),
    }
