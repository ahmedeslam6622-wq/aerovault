"""User model — accounts, roles, notification preferences."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone
import enum


class UserRole(str, enum.Enum):
    VIEWER        = "viewer"
    FLIGHT_MANAGER= "flight_manager"
    MAINT_CHIEF   = "maintenance_chief"
    ADMIN         = "admin"
    SUPERUSER     = "superuser"


class NotificationMode(str, enum.Enum):
    WORK     = "work"      # Nearly everything
    STANDARD = "standard"  # Important updates only
    MINIMAL  = "minimal"   # Critical only


class User(Base):
    __tablename__ = "users"

    id                  = Column(Integer, primary_key=True, index=True)
    username            = Column(String(64),  unique=True, nullable=False, index=True)
    full_name           = Column(String(128), nullable=False)
    email               = Column(String(128), unique=True, nullable=False)
    department          = Column(String(64),  nullable=True)
    employee_id         = Column(String(32),  unique=True, nullable=False)
    hashed_password     = Column(String(256), nullable=False)
    totp_secret         = Column(String(64),  nullable=True)   # Superuser only
    role                = Column(SAEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    notification_mode   = Column(SAEnum(NotificationMode), default=NotificationMode.STANDARD)
    is_active           = Column(Boolean, default=True)
    created_at          = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login          = Column(DateTime, nullable=True)
    avatar_initials     = Column(String(4),   nullable=True)   # e.g. "JD" for John Doe

    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username} [{self.role}]>"
