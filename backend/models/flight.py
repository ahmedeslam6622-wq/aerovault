"""Flight model — complete operational flight record."""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone
import enum


class FlightStatus(str, enum.Enum):
    SCHEDULED   = "scheduled"
    BOARDING    = "boarding"
    DEPARTED    = "departed"
    EN_ROUTE    = "en_route"
    APPROACHING = "approaching"
    LANDED      = "landed"
    DELAYED     = "delayed"
    CANCELLED   = "cancelled"
    DIVERTED    = "diverted"
    ON_GROUND   = "on_ground"   # Arrived but not at gate yet


class FlightType(str, enum.Enum):
    DOMESTIC      = "domestic"
    INTERNATIONAL = "international"
    CARGO         = "cargo"
    CHARTER       = "charter"


class Flight(Base):
    __tablename__ = "flights"

    id               = Column(Integer, primary_key=True, index=True)

    # Identifiers
    flight_number    = Column(String(16),  nullable=False, index=True)   # e.g. "EK204"
    airline_iata     = Column(String(4),   nullable=False)                # e.g. "EK"
    airline_name     = Column(String(64),  nullable=False)                # e.g. "Emirates"
    callsign         = Column(String(16),  nullable=True)                 # e.g. "UAE204"

    # Route
    origin_iata      = Column(String(4),   nullable=False)                # e.g. "DXB"
    origin_city      = Column(String(64),  nullable=False)
    origin_country   = Column(String(64),  nullable=False)
    dest_iata        = Column(String(4),   nullable=False)
    dest_city        = Column(String(64),  nullable=False)
    dest_country     = Column(String(64),  nullable=False)

    # Aircraft
    aircraft_reg     = Column(String(16),  nullable=False)                # e.g. "A6-EDP"
    aircraft_type    = Column(String(32),  nullable=False)                # e.g. "Boeing 777-300ER"
    aircraft_icao    = Column(String(8),   nullable=True)                 # e.g. "B77W"

    # Schedule
    flight_type      = Column(SAEnum(FlightType), default=FlightType.INTERNATIONAL)
    scheduled_dep    = Column(DateTime, nullable=False)
    scheduled_arr    = Column(DateTime, nullable=False)
    estimated_dep    = Column(DateTime, nullable=True)
    estimated_arr    = Column(DateTime, nullable=True)
    actual_dep       = Column(DateTime, nullable=True)
    actual_arr       = Column(DateTime, nullable=True)
    delay_minutes    = Column(Integer,  default=0)
    delay_reason     = Column(String(128), nullable=True)

    # Gate & Terminal
    terminal         = Column(String(8),   nullable=True)                 # e.g. "T3"
    gate             = Column(String(8),   nullable=True)                 # e.g. "G14"
    check_in_desk    = Column(String(16),  nullable=True)                 # e.g. "D21-D26"
    baggage_belt     = Column(String(8),   nullable=True)                 # e.g. "Belt 7"

    # Status
    status           = Column(SAEnum(FlightStatus), default=FlightStatus.SCHEDULED)
    altitude_ft      = Column(Integer,  nullable=True)
    speed_kts        = Column(Integer,  nullable=True)
    latitude         = Column(Float,    nullable=True)
    longitude        = Column(Float,    nullable=True)

    # Capacity
    total_seats      = Column(Integer,  nullable=True)
    passengers_booked= Column(Integer,  nullable=True)
    cargo_kg         = Column(Float,    nullable=True)
    fuel_kg          = Column(Float,    nullable=True)

    # Flags
    is_codeshare     = Column(Boolean,  default=False)
    codeshare_with   = Column(String(32), nullable=True)
    is_charter       = Column(Boolean,  default=False)
    remarks          = Column(Text,     nullable=True)

    created_at       = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at       = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                              onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    crew_assignments = relationship("CrewAssignment", back_populates="flight", cascade="all, delete-orphan")
    maintenance_logs = relationship("MaintenanceLog",  back_populates="flight")

    def __repr__(self):
        return f"<Flight {self.flight_number} {self.origin_iata}→{self.dest_iata}>"
