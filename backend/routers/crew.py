"""Crew router — crew members, assignments, hours tracking."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from database import get_db
from models import CrewMember, CrewAssignment, CrewRole, CrewStatus, Flight, User
from auth.dependencies import get_current_user, require_flight_manager

router = APIRouter()


def crew_to_dict(c: CrewMember) -> dict:
    return {
        "id":                 c.id,
        "employee_id":        c.employee_id,
        "full_name":          c.full_name,
        "nationality":        c.nationality,
        "role":               c.role.value,
        "status":             c.status.value,
        "base_airport":       c.base_airport,
        "current_airport":    c.current_airport,
        "flight_hours_total": c.flight_hours_total,
        "flight_hours_month": c.flight_hours_month,
        "flight_hours_year":  c.flight_hours_year,
        "max_hours_month":    c.max_hours_month,
        "max_hours_year":     c.max_hours_year,
        "duty_hours_today":   c.duty_hours_today,
        "max_duty_hours":     c.max_duty_hours,
        "license_type":       c.license_type.value if c.license_type else None,
        "license_number":     c.license_number,
        "license_expiry":     c.license_expiry,
        "medical_class":      c.medical_class,
        "medical_expiry":     c.medical_expiry,
        "type_ratings":       c.type_ratings or [],
        "languages":          c.languages or [],
        "hours_remaining_month": max(0, c.max_hours_month - c.flight_hours_month),
        "hours_remaining_year":  max(0, c.max_hours_year  - c.flight_hours_year),
        "active_assignments": len([a for a in c.assignments]),
        "notes":              c.notes,
    }


@router.get("/")
async def list_crew(
    status:  Optional[str] = Query(None),
    role:    Optional[str] = Query(None),
    airport: Optional[str] = Query(None),
    search:  Optional[str] = Query(None),
    db:      Session = Depends(get_db),
    _user:   User    = Depends(get_current_user),
):
    q = db.query(CrewMember)
    if status:
        q = q.filter(CrewMember.status == status)
    if role:
        q = q.filter(CrewMember.role == role)
    if airport:
        q = q.filter(CrewMember.current_airport == airport.upper())
    if search:
        s = f"%{search}%"
        q = q.filter(
            CrewMember.full_name.ilike(s) |
            CrewMember.employee_id.ilike(s)
        )
    crew = q.order_by(CrewMember.role, CrewMember.full_name).all()
    return {"total": len(crew), "crew": [crew_to_dict(c) for c in crew]}


@router.get("/available")
async def list_available_crew(
    aircraft_icao: Optional[str] = Query(None),
    role:          Optional[str] = Query(None),
    db:            Session = Depends(get_db),
    _user:         User    = Depends(get_current_user),
):
    """Return crew that can be assigned: available or standby, within hours limits."""
    q = db.query(CrewMember).filter(
        CrewMember.status.in_([CrewStatus.AVAILABLE, CrewStatus.STANDBY])
    )
    if role:
        q = q.filter(CrewMember.role == role)
    crew = q.all()

    # Filter by type rating if aircraft specified
    if aircraft_icao:
        crew = [c for c in crew if aircraft_icao.upper() in (c.type_ratings or [])]

    # Filter out those at hours limit
    crew = [c for c in crew if c.flight_hours_month < c.max_hours_month]

    return {"total": len(crew), "crew": [crew_to_dict(c) for c in crew]}


@router.get("/{crew_id}")
async def get_crew_member(
    crew_id: int,
    db:      Session = Depends(get_db),
    _user:   User    = Depends(get_current_user),
):
    c = db.query(CrewMember).filter(CrewMember.id == crew_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Crew member not found.")
    data = crew_to_dict(c)
    data["assignments"] = [
        {
            "flight_number":  a.flight.flight_number,
            "route":          f"{a.flight.origin_iata}→{a.flight.dest_iata}",
            "status":         a.flight.status.value,
            "scheduled_dep":  a.flight.scheduled_dep.isoformat() if a.flight.scheduled_dep else None,
            "role_on_flight": a.role_on_flight.value,
        }
        for a in c.assignments
    ]
    return data


class AssignCrewBody(BaseModel):
    flight_id:      int
    crew_member_id: int
    role_on_flight: str


@router.post("/assign")
async def assign_crew(
    body: AssignCrewBody,
    db:   Session = Depends(get_db),
    user: User    = Depends(require_flight_manager),
):
    flight = db.query(Flight).filter(Flight.id == body.flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found.")
    crew = db.query(CrewMember).filter(CrewMember.id == body.crew_member_id).first()
    if not crew:
        raise HTTPException(status_code=404, detail="Crew member not found.")

    # Check hours
    if crew.flight_hours_month >= crew.max_hours_month:
        raise HTTPException(
            status_code=409,
            detail=f"{crew.full_name} has reached the monthly hours limit ({crew.max_hours_month}h)."
        )

    # Check type rating
    if flight.aircraft_icao and flight.aircraft_icao not in (crew.type_ratings or []):
        raise HTTPException(
            status_code=409,
            detail=f"{crew.full_name} does not hold a type rating for {flight.aircraft_icao}.",
        )

    try:
        role = CrewRole(body.role_on_flight)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {body.role_on_flight}")

    assignment = CrewAssignment(
        flight_id=body.flight_id,
        crew_member_id=body.crew_member_id,
        role_on_flight=role,
        assigned_by=user.username,
    )
    db.add(assignment)
    db.commit()
    return {"message": f"{crew.full_name} assigned to {flight.flight_number} as {role.value}."}


class StatusUpdate(BaseModel):
    status: str


@router.patch("/{crew_id}/status")
async def update_crew_status(
    crew_id: int,
    body:    StatusUpdate,
    db:      Session = Depends(get_db),
    _user:   User    = Depends(require_flight_manager),
):
    c = db.query(CrewMember).filter(CrewMember.id == crew_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Crew member not found.")
    try:
        c.status = CrewStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")
    db.commit()
    return {"message": f"Status updated to {body.status}."}


@router.get("/stats/summary")
async def crew_stats(
    db:  Session = Depends(get_db),
    _u:  User    = Depends(get_current_user),
):
    from sqlalchemy import func
    total       = db.query(func.count(CrewMember.id)).scalar()
    by_status   = db.query(CrewMember.status, func.count(CrewMember.id)).group_by(CrewMember.status).all()
    by_role     = db.query(CrewMember.role,   func.count(CrewMember.id)).group_by(CrewMember.role).all()
    on_duty     = db.query(func.count(CrewMember.id)).filter(CrewMember.status == CrewStatus.ON_DUTY).scalar()
    available   = db.query(func.count(CrewMember.id)).filter(CrewMember.status == CrewStatus.AVAILABLE).scalar()
    standby     = db.query(func.count(CrewMember.id)).filter(CrewMember.status == CrewStatus.STANDBY).scalar()

    return {
        "total": total,
        "on_duty": on_duty,
        "available": available,
        "standby": standby,
        "by_status": {s.value: c for s, c in by_status},
        "by_role":   {r.value: c for r, c in by_role},
    }
