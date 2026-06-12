"""Crew model — staff profiles, certifications, and flight assignments."""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Enum as SAEnum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone
import enum


class CrewRole(str, enum.Enum):
    CAPTAIN          = "captain"
    FIRST_OFFICER    = "first_officer"
    SECOND_OFFICER   = "second_officer"           # Long-haul relief
    PURSER           = "purser"                    # Senior cabin crew
    SENIOR_CABIN     = "senior_cabin_crew"
    CABIN_CREW       = "cabin_crew"
    GROUND_AGENT     = "ground_agent"
    DISPATCHER       = "flight_dispatcher"
    LOAD_CONTROLLER  = "load_controller"


class CrewStatus(str, enum.Enum):
    AVAILABLE    = "available"
    ON_DUTY      = "on_duty"
    RESTING      = "resting"           # Mandatory rest period
    ON_LEAVE     = "on_leave"
    SICK         = "sick"
    STANDBY      = "standby"           # Reserve crew, on-call
    GROUNDED     = "grounded"          # Medical / regulatory hold
    OFF_ROSTER   = "off_roster"


class LicenseType(str, enum.Enum):
    ATPL   = "ATPL"   # Airline Transport Pilot License
    CPL    = "CPL"    # Commercial Pilot License
    IR     = "IR"     # Instrument Rating
    CABIN  = "CABIN"  # Cabin Crew Certificate
    GROUND = "GROUND" # Ground Operations Certificate


class CrewMember(Base):
    __tablename__ = "crew_members"

    id                  = Column(Integer,  primary_key=True, index=True)
    employee_id         = Column(String(16), unique=True, nullable=False, index=True)  # e.g. "P-00142"
    full_name           = Column(String(128), nullable=False)
    nationality         = Column(String(64),  nullable=True)
    date_of_birth       = Column(String(16),  nullable=True)                           # ISO date string
    gender              = Column(String(16),  nullable=True)

    # Role & Status
    role                = Column(SAEnum(CrewRole),   nullable=False)
    status              = Column(SAEnum(CrewStatus), default=CrewStatus.AVAILABLE)
    base_airport        = Column(String(4),  nullable=False)                            # IATA, e.g. "CAI"
    current_airport     = Column(String(4),  nullable=True)

    # Hours tracking — regulatory compliance
    flight_hours_total  = Column(Float,  default=0.0)
    flight_hours_month  = Column(Float,  default=0.0)   # Current month
    flight_hours_year   = Column(Float,  default=0.0)   # Current year
    max_hours_month     = Column(Float,  default=100.0) # ICAO limit
    max_hours_year      = Column(Float,  default=1000.0)
    duty_hours_today    = Column(Float,  default=0.0)
    max_duty_hours      = Column(Float,  default=14.0)  # Flight Duty Period limit

    # Licensing
    license_type        = Column(SAEnum(LicenseType), nullable=True)
    license_number      = Column(String(32),  nullable=True)
    license_expiry      = Column(String(16),  nullable=True)
    medical_class       = Column(String(8),   nullable=True)   # Class 1, Class 2
    medical_expiry      = Column(String(16),  nullable=True)

    # Aircraft type ratings (list of ICAO codes this crew is rated on)
    type_ratings        = Column(JSON, default=list)  # e.g. ["B77W", "A388", "B738"]

    # Languages
    languages           = Column(JSON, default=list)  # e.g. ["Arabic", "English", "French"]

    # Contact
    phone               = Column(String(32),  nullable=True)
    email               = Column(String(128), nullable=True)

    # Rest tracking
    last_duty_end       = Column(DateTime, nullable=True)
    min_rest_hours      = Column(Float,  default=11.0)   # Minimum required rest

    # Notes
    notes               = Column(Text, nullable=True)

    created_at          = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at          = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                                 onupdate=lambda: datetime.now(timezone.utc))

    assignments         = relationship("CrewAssignment", back_populates="crew_member", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Crew {self.employee_id} {self.full_name} [{self.role}]>"


class CrewAssignment(Base):
    __tablename__ = "crew_assignments"

    id              = Column(Integer, primary_key=True, index=True)
    flight_id       = Column(Integer, ForeignKey("flights.id"),       nullable=False)
    crew_member_id  = Column(Integer, ForeignKey("crew_members.id"),  nullable=False)
    role_on_flight  = Column(SAEnum(CrewRole), nullable=False)
    assigned_at     = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    assigned_by     = Column(String(64), nullable=True)   # Username of assigner
    notes           = Column(Text, nullable=True)

    flight          = relationship("Flight",     back_populates="crew_assignments")
    crew_member     = relationship("CrewMember", back_populates="assignments")

    def __repr__(self):
        return f"<Assignment Flight#{self.flight_id} → {self.crew_member_id}>"
