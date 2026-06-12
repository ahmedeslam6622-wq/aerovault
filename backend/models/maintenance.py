"""
Maintenance model — deep aviation maintenance tracking.

Covers:
  - Aircraft fleet registry
  - Scheduled / unscheduled maintenance tasks
  - MEL (Minimum Equipment List) items
  - AOG (Aircraft on Ground) incidents
  - Component lifecycle tracking
  - Inspector / technician assignments
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Enum as SAEnum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone
import enum


# ─── Aircraft Check Types ──────────────────────────────────────────────────

class CheckType(str, enum.Enum):
    TRANSIT     = "transit"        # Quick turnaround check between flights (~15 min)
    PRE_FLIGHT  = "pre_flight"     # Full pre-departure walkround
    A_CHECK     = "a_check"        # Light check every ~500 flight hours
    B_CHECK     = "b_check"        # Every ~3–6 months (some airlines merge with A)
    C_CHECK     = "c_check"        # Heavy check every ~18–24 months, ~2 weeks hangar
    D_CHECK     = "d_check"        # Full overhaul every ~6–12 years, ~2 months hangar
    ENGINE_BORESCOPE = "engine_borescope"
    LANDING_GEAR     = "landing_gear_inspection"
    AVIONICS         = "avionics_check"
    CABIN            = "cabin_inspection"
    AD_COMPLIANCE    = "airworthiness_directive"  # Mandatory FAA/EASA directive
    UNSCHEDULED      = "unscheduled"


class MaintStatus(str, enum.Enum):
    SCHEDULED    = "scheduled"
    IN_PROGRESS  = "in_progress"
    ON_HOLD      = "on_hold"        # Waiting for part / approval
    COMPLETED    = "completed"
    DEFERRED     = "deferred"       # MEL deferral approved
    CANCELLED    = "cancelled"
    OVERDUE      = "overdue"


class AOGStatus(str, enum.Enum):
    ACTIVE       = "active"         # Aircraft grounded right now
    RECOVERING   = "recovering"     # Parts en route / work started
    CLEARED      = "cleared"        # Returned to service
    TRANSFERRED  = "transferred"    # Sent to MRO facility


class Priority(str, enum.Enum):
    ROUTINE    = "routine"
    URGENT     = "urgent"
    AOG        = "aog"              # Highest — aircraft on ground


# ─── Aircraft Fleet Registry ───────────────────────────────────────────────

class Aircraft(Base):
    __tablename__ = "aircraft"

    id                  = Column(Integer,  primary_key=True, index=True)
    registration        = Column(String(16),  unique=True, nullable=False, index=True)  # e.g. "SU-GEA"
    airline_iata        = Column(String(4),   nullable=False)
    airline_name        = Column(String(64),  nullable=False)
    aircraft_type       = Column(String(32),  nullable=False)       # e.g. "Airbus A320-214"
    icao_type           = Column(String(8),   nullable=True)        # e.g. "A320"
    manufacturer        = Column(String(32),  nullable=False)       # "Airbus" / "Boeing"
    msn                 = Column(String(16),  nullable=True)        # Manufacturer Serial Number
    year_of_manufacture = Column(Integer,     nullable=True)
    delivery_date       = Column(String(16),  nullable=True)

    # Engines
    engine_type         = Column(String(64),  nullable=True)        # e.g. "CFM56-5B6/3"
    engine_count        = Column(Integer,     default=2)

    # Airframe life tracking
    total_flight_hours  = Column(Float,   default=0.0)
    total_cycles        = Column(Integer, default=0)   # Pressurization cycles (take-off/land pairs)
    max_cycles          = Column(Integer, nullable=True)
    hours_since_last_a  = Column(Float,   default=0.0)
    hours_since_last_c  = Column(Float,   default=0.0)
    next_a_check_due    = Column(String(16), nullable=True)   # ISO date
    next_c_check_due    = Column(String(16), nullable=True)

    # Status
    is_active           = Column(Boolean, default=True)
    is_aog              = Column(Boolean, default=False)
    current_airport     = Column(String(4),  nullable=True)
    home_base           = Column(String(4),  nullable=True)

    # Certificates
    airworthiness_cert  = Column(String(32), nullable=True)
    cert_expiry         = Column(String(16), nullable=True)
    noise_cert          = Column(String(16), nullable=True)   # ICAO Chapter

    notes               = Column(Text, nullable=True)
    created_at          = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at          = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                                 onupdate=lambda: datetime.now(timezone.utc))

    maintenance_logs    = relationship("MaintenanceLog",  back_populates="aircraft", cascade="all, delete-orphan")
    mel_items           = relationship("MELItem",         back_populates="aircraft", cascade="all, delete-orphan")
    aog_records         = relationship("AOGRecord",       back_populates="aircraft", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Aircraft {self.registration} ({self.aircraft_type})>"


# ─── Maintenance Log ───────────────────────────────────────────────────────

class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"

    id               = Column(Integer, primary_key=True, index=True)
    aircraft_id      = Column(Integer, ForeignKey("aircraft.id"), nullable=False)
    flight_id        = Column(Integer, ForeignKey("flights.id"),  nullable=True)  # If tied to a flight

    task_number      = Column(String(32), unique=True, nullable=False)  # e.g. "MNT-2024-00341"
    check_type       = Column(SAEnum(CheckType),   nullable=False)
    status           = Column(SAEnum(MaintStatus), default=MaintStatus.SCHEDULED)
    priority         = Column(SAEnum(Priority),    default=Priority.ROUTINE)

    title            = Column(String(128), nullable=False)
    description      = Column(Text,        nullable=True)
    ata_chapter      = Column(String(16),  nullable=True)   # ATA 100 chapter code e.g. "ATA 32" (Landing Gear)
    ata_description  = Column(String(64),  nullable=True)   # e.g. "Landing Gear"

    # Scheduling
    scheduled_start  = Column(DateTime, nullable=True)
    scheduled_end    = Column(DateTime, nullable=True)
    actual_start     = Column(DateTime, nullable=True)
    actual_end       = Column(DateTime, nullable=True)

    # Labor
    lead_technician  = Column(String(128), nullable=True)
    technicians      = Column(JSON, default=list)           # List of names
    hangar_bay       = Column(String(16),  nullable=True)   # e.g. "Hangar 3, Bay B"
    man_hours_est    = Column(Float,  nullable=True)
    man_hours_actual = Column(Float,  nullable=True)

    # Parts
    parts_required   = Column(JSON, default=list)           # [{part_number, description, qty, status}]
    parts_cost_usd   = Column(Float, default=0.0)
    labor_cost_usd   = Column(Float, default=0.0)

    # Compliance
    work_order_ref   = Column(String(32), nullable=True)
    ad_number        = Column(String(32), nullable=True)    # Airworthiness Directive number
    sb_number        = Column(String(32), nullable=True)    # Service Bulletin number
    approved_by      = Column(String(128), nullable=True)   # Licensed Aircraft Engineer
    license_number   = Column(String(32),  nullable=True)
    sign_off_time    = Column(DateTime, nullable=True)

    findings         = Column(Text, nullable=True)          # What was actually found
    corrective_action= Column(Text, nullable=True)
    next_due_hours   = Column(Float,  nullable=True)        # Next check trigger
    next_due_date    = Column(String(16), nullable=True)

    created_at       = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at       = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                               onupdate=lambda: datetime.now(timezone.utc))

    aircraft         = relationship("Aircraft", back_populates="maintenance_logs")
    flight           = relationship("Flight",   back_populates="maintenance_logs")

    def __repr__(self):
        return f"<MaintLog {self.task_number} [{self.status}]>"


# ─── MEL Items (Minimum Equipment List) ───────────────────────────────────

class MELItem(Base):
    """
    MEL items allow aircraft to dispatch with known defects under controlled conditions.
    Each item has a category (A/B/C/D) defining the deferral window.
    """
    __tablename__ = "mel_items"

    id              = Column(Integer, primary_key=True, index=True)
    aircraft_id     = Column(Integer, ForeignKey("aircraft.id"), nullable=False)
    mel_number      = Column(String(32), nullable=False)        # e.g. "MEL-32-41-01A"
    ata_chapter     = Column(String(8),  nullable=True)
    description     = Column(String(256), nullable=False)       # What's deferred
    category        = Column(String(4),  nullable=False)        # A (3 days), B (3 days), C (10 days), D (120 days)
    dispatch_conditions = Column(Text, nullable=True)           # What crew/ops must do to dispatch legally
    raised_date     = Column(String(16), nullable=False)
    expiry_date     = Column(String(16), nullable=False)
    is_active       = Column(Boolean, default=True)
    closed_date     = Column(String(16), nullable=True)
    raised_by       = Column(String(128), nullable=True)

    aircraft        = relationship("Aircraft", back_populates="mel_items")

    def __repr__(self):
        return f"<MEL {self.mel_number} Cat-{self.category}>"


# ─── AOG Records ──────────────────────────────────────────────────────────

class AOGRecord(Base):
    """Aircraft on Ground — serious unplanned grounding events."""
    __tablename__ = "aog_records"

    id              = Column(Integer, primary_key=True, index=True)
    aircraft_id     = Column(Integer, ForeignKey("aircraft.id"), nullable=False)
    aog_ref         = Column(String(32), unique=True, nullable=False)   # e.g. "AOG-2024-0089"
    status          = Column(SAEnum(AOGStatus), default=AOGStatus.ACTIVE)
    location        = Column(String(4),  nullable=False)    # Airport IATA where grounded
    fault_description = Column(Text,     nullable=False)
    ata_chapter     = Column(String(16), nullable=True)
    grounded_at     = Column(DateTime,   nullable=False)
    cleared_at      = Column(DateTime,   nullable=True)
    affected_flights= Column(JSON, default=list)             # Flight numbers impacted
    parts_on_order  = Column(JSON, default=list)             # Part numbers being sourced
    go_team_dispatched = Column(Boolean, default=False)      # MRO go-team sent?
    estimated_tat   = Column(String(64), nullable=True)      # Estimated turnaround time
    notes           = Column(Text, nullable=True)
    created_at      = Column(DateTime,   default=lambda: datetime.now(timezone.utc))

    aircraft        = relationship("Aircraft", back_populates="aog_records")

    def __repr__(self):
        return f"<AOG {self.aog_ref} [{self.status}]>"
