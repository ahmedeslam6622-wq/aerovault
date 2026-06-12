"""Flights router — list, detail, update, with live OpenSky position overlay."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_db
from models import Flight, FlightStatus, User
from auth.dependencies import get_current_user, require_flight_manager
from opensky import fetch_egyptair_positions, merge_flight_with_live

router = APIRouter()


def flight_to_dict(f: Flight) -> dict:
    return {
        "id":               f.id,
        "flight_number":    f.flight_number,
        "airline_iata":     f.airline_iata,
        "airline_name":     f.airline_name,
        "callsign":         f.callsign,
        "origin_iata":      f.origin_iata,
        "origin_city":      f.origin_city,
        "origin_country":   f.origin_country,
        "dest_iata":        f.dest_iata,
        "dest_city":        f.dest_city,
        "dest_country":     f.dest_country,
        "aircraft_reg":     f.aircraft_reg,
        "aircraft_type":    f.aircraft_type,
        "aircraft_icao":    f.aircraft_icao,
        "flight_type":      f.flight_type.value if f.flight_type else None,
        "scheduled_dep":    f.scheduled_dep.isoformat() if f.scheduled_dep else None,
        "scheduled_arr":    f.scheduled_arr.isoformat() if f.scheduled_arr else None,
        "estimated_dep":    f.estimated_dep.isoformat() if f.estimated_dep else None,
        "estimated_arr":    f.estimated_arr.isoformat() if f.estimated_arr else None,
        "actual_dep":       f.actual_dep.isoformat() if f.actual_dep else None,
        "actual_arr":       f.actual_arr.isoformat() if f.actual_arr else None,
        "delay_minutes":    f.delay_minutes,
        "delay_reason":     f.delay_reason,
        "terminal":         f.terminal,
        "gate":             f.gate,
        "check_in_desk":    f.check_in_desk,
        "baggage_belt":     f.baggage_belt,
        "status":           f.status.value if f.status else None,
        "altitude_ft":      f.altitude_ft,
        "speed_kts":        f.speed_kts,
        "latitude":         f.latitude,
        "longitude":        f.longitude,
        "total_seats":      f.total_seats,
        "passengers_booked":f.passengers_booked,
        "cargo_kg":         f.cargo_kg,
        "fuel_kg":          f.fuel_kg,
        "is_codeshare":     f.is_codeshare,
        "remarks":          f.remarks,
        "updated_at":       f.updated_at.isoformat() if f.updated_at else None,
        "crew_count":       len(f.crew_assignments),
        "live_tracking":    False,
    }


@router.get("/")
async def list_flights(
    status:  Optional[str] = Query(None),
    type:    Optional[str] = Query(None),
    search:  Optional[str] = Query(None),
    live:    bool          = Query(True),
    limit:   int           = Query(50, le=200),
    offset:  int           = Query(0),
    db:      Session       = Depends(get_db),
    _user:   User          = Depends(get_current_user),
):
    q = db.query(Flight)
    if status:
        q = q.filter(Flight.status == status)
    if type:
        q = q.filter(Flight.flight_type == type)
    if search:
        s = f"%{search.upper()}%"
        q = q.filter(
            Flight.flight_number.like(s) |
            Flight.origin_iata.like(s)   |
            Flight.dest_iata.like(s)     |
            Flight.aircraft_reg.like(s)
        )
    total   = q.count()
    flights = q.order_by(Flight.scheduled_dep).offset(offset).limit(limit).all()
    result  = [flight_to_dict(f) for f in flights]

    # Overlay live OpenSky positions
    if live:
        try:
            positions = await fetch_egyptair_positions()
            if positions:
                result = [merge_flight_with_live(f, positions) for f in result]
        except Exception:
            pass  # Never break the page if OpenSky is down

    return {"total": total, "flights": result, "live_data": live}


@router.get("/stats/summary")
async def flight_stats(
    db:  Session = Depends(get_db),
    _u:  User    = Depends(get_current_user),
):
    from sqlalchemy import func
    total     = db.query(func.count(Flight.id)).scalar()
    by_status = db.query(Flight.status, func.count(Flight.id)).group_by(Flight.status).all()
    delayed   = db.query(func.count(Flight.id)).filter(Flight.delay_minutes > 0).scalar()
    cancelled = db.query(func.count(Flight.id)).filter(Flight.status == FlightStatus.CANCELLED).scalar()
    return {
        "total": total,
        "delayed": delayed,
        "cancelled": cancelled,
        "by_status": {s.value: c for s, c in by_status},
    }


@router.get("/{flight_id}")
async def get_flight(
    flight_id: int,
    db:        Session = Depends(get_db),
    _user:     User    = Depends(get_current_user),
):
    f = db.query(Flight).filter(Flight.id == flight_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Flight not found.")
    data = flight_to_dict(f)

    # Try live position for this specific flight
    try:
        positions = await fetch_egyptair_positions()
        if positions:
            data = merge_flight_with_live(data, positions)
    except Exception:
        pass

    data["crew"] = [
        {
            "employee_id": a.crew_member.employee_id,
            "full_name":   a.crew_member.full_name,
            "role":        a.role_on_flight.value,
            "status":      a.crew_member.status.value,
        }
        for a in f.crew_assignments
    ]
    return data


class FlightUpdate(BaseModel):
    status:         Optional[str]      = None
    gate:           Optional[str]      = None
    terminal:       Optional[str]      = None
    delay_minutes:  Optional[int]      = None
    delay_reason:   Optional[str]      = None
    estimated_dep:  Optional[datetime] = None
    estimated_arr:  Optional[datetime] = None
    baggage_belt:   Optional[str]      = None
    check_in_desk:  Optional[str]      = None
    remarks:        Optional[str]      = None


@router.patch("/{flight_id}")
async def update_flight(
    flight_id: int,
    update:    FlightUpdate,
    db:        Session = Depends(get_db),
    user:      User    = Depends(require_flight_manager),
):
    f = db.query(Flight).filter(Flight.id == flight_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Flight not found.")
    if update.status:
        try:    f.status = FlightStatus(update.status)
        except: raise HTTPException(status_code=400, detail=f"Invalid status: {update.status}")
    if update.gate          is not None: f.gate          = update.gate
    if update.terminal      is not None: f.terminal      = update.terminal
    if update.delay_minutes is not None: f.delay_minutes = update.delay_minutes
    if update.delay_reason  is not None: f.delay_reason  = update.delay_reason
    if update.estimated_dep is not None: f.estimated_dep = update.estimated_dep
    if update.estimated_arr is not None: f.estimated_arr = update.estimated_arr
    if update.baggage_belt  is not None: f.baggage_belt  = update.baggage_belt
    if update.check_in_desk is not None: f.check_in_desk = update.check_in_desk
    if update.remarks       is not None: f.remarks       = update.remarks
    db.commit()
    db.refresh(f)
    return flight_to_dict(f)
