"""Notification model — system alerts per user and mode."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone
import enum


class NotifCategory(str, enum.Enum):
    GATE_CHANGE        = "gate_change"
    DELAY              = "delay"
    CANCELLATION       = "cancellation"
    CREW_REASSIGNMENT  = "crew_reassignment"
    MAINTENANCE_ALERT  = "maintenance_alert"
    AOG                = "aog"
    EMERGENCY          = "emergency"
    GROUNDING          = "grounding"
    CRITICAL_MAINT     = "critical_maintenance"
    SYSTEM             = "system"


# Which modes receive which categories
MODE_CATEGORIES = {
    "work":     ["gate_change", "delay", "cancellation", "crew_reassignment",
                 "maintenance_alert", "aog", "emergency", "grounding", "critical_maintenance", "system"],
    "standard": ["delay", "cancellation", "aog", "emergency", "grounding", "critical_maintenance"],
    "minimal":  ["emergency", "grounding", "aog"],
}


class Notification(Base):
    __tablename__ = "notifications"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    category    = Column(SAEnum(NotifCategory), nullable=False)
    title       = Column(String(128), nullable=False)
    body        = Column(Text, nullable=False)
    flight_ref  = Column(String(16), nullable=True)   # Flight number if relevant
    aircraft_ref= Column(String(16), nullable=True)
    is_read     = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user        = relationship("User", back_populates="notifications")
