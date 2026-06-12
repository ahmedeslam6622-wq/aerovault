"""Notifications router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models import User, Notification, NotifCategory
from models.notification import MODE_CATEGORIES
from models.user import NotificationMode
from auth.dependencies import get_current_user

router = APIRouter()


@router.get("/")
async def get_my_notifications(
    unread_only: bool = False,
    limit: int = 50,
    db:    Session = Depends(get_db),
    user:  User    = Depends(get_current_user),
):
    # Filter by the user's notification mode
    allowed = MODE_CATEGORIES.get(user.notification_mode.value, [])
    q = db.query(Notification).filter(
        Notification.user_id == user.id,
        Notification.category.in_(allowed),
    )
    if unread_only:
        q = q.filter(Notification.is_read == False)
    notifications = q.order_by(Notification.created_at.desc()).limit(limit).all()
    return {
        "total": len(notifications),
        "mode":  user.notification_mode.value,
        "notifications": [
            {
                "id":          n.id,
                "category":    n.category.value,
                "title":       n.title,
                "body":        n.body,
                "flight_ref":  n.flight_ref,
                "aircraft_ref":n.aircraft_ref,
                "is_read":     n.is_read,
                "created_at":  n.created_at.isoformat(),
            }
            for n in notifications
        ],
    }


@router.patch("/{notif_id}/read")
async def mark_read(notif_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    n = db.query(Notification).filter(Notification.id == notif_id, Notification.user_id == user.id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found.")
    n.is_read = True
    db.commit()
    return {"message": "Marked as read."}


@router.patch("/read-all")
async def mark_all_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read == False).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read."}


class ModeUpdate(BaseModel):
    mode: str


@router.patch("/settings/mode")
async def update_notification_mode(
    body: ModeUpdate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    try:
        user.notification_mode = NotificationMode(body.mode)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {body.mode}. Use: work, standard, minimal")
    db.commit()
    return {"message": f"Notification mode updated to {body.mode}.", "mode": body.mode}
