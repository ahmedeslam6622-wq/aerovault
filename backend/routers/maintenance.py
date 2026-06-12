"""Maintenance router — aircraft fleet, maintenance tasks, MEL items, AOG records."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Any

from database import get_db
from models import Aircraft, MaintenanceLog, MELItem, AOGRecord, User
from models.maintenance import MaintStatus, Priority, CheckType, AOGStatus
from auth.dependencies import get_current_user, require_maintenance_chief

router = APIRouter()


# ─── Aircraft ─────────────────────────────────────────────────────────────

def aircraft_to_dict(a: Aircraft) -> dict:
    return {
        "id":                  a.id,
        "registration":        a.registration,
        "airline_iata":        a.airline_iata,
        "airline_name":        a.airline_name,
        "aircraft_type":       a.aircraft_type,
        "icao_type":           a.icao_type,
        "manufacturer":        a.manufacturer,
        "msn":                 a.msn,
        "year_of_manufacture": a.year_of_manufacture,
        "engine_type":         a.engine_type,
        "engine_count":        a.engine_count,
        "total_flight_hours":  a.total_flight_hours,
        "total_cycles":        a.total_cycles,
        "hours_since_last_a":  a.hours_since_last_a,
        "hours_since_last_c":  a.hours_since_last_c,
        "next_a_check_due":    a.next_a_check_due,
        "next_c_check_due":    a.next_c_check_due,
        "is_active":           a.is_active,
        "is_aog":              a.is_aog,
        "current_airport":     a.current_airport,
        "home_base":           a.home_base,
        "airworthiness_cert":  a.airworthiness_cert,
        "cert_expiry":         a.cert_expiry,
        "open_mel_items":      len([m for m in a.mel_items if m.is_active]),
        "active_aog":          len([g for g in a.aog_records if g.status == AOGStatus.ACTIVE]),
        "notes":               a.notes,
    }


@router.get("/aircraft")
async def list_aircraft(
    is_aog:   Optional[bool] = Query(None),
    airport:  Optional[str]  = Query(None),
    db:       Session = Depends(get_db),
    _user:    User    = Depends(get_current_user),
):
    q = db.query(Aircraft)
    if is_aog is not None:
        q = q.filter(Aircraft.is_aog == is_aog)
    if airport:
        q = q.filter(Aircraft.current_airport == airport.upper())
    aircraft = q.order_by(Aircraft.registration).all()
    return {"total": len(aircraft), "aircraft": [aircraft_to_dict(a) for a in aircraft]}


@router.get("/aircraft/{ac_id}")
async def get_aircraft(
    ac_id: int,
    db:    Session = Depends(get_db),
    _user: User    = Depends(get_current_user),
):
    a = db.query(Aircraft).filter(Aircraft.id == ac_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Aircraft not found.")
    data = aircraft_to_dict(a)
    data["maintenance_logs"] = [_log_summary(l) for l in a.maintenance_logs]
    data["mel_items"]        = [_mel_summary(m) for m in a.mel_items if m.is_active]
    data["aog_records"]      = [_aog_summary(g) for g in a.aog_records]
    return data


# ─── Maintenance Logs ─────────────────────────────────────────────────────

def _log_summary(l: MaintenanceLog) -> dict:
    return {
        "id":               l.id,
        "task_number":      l.task_number,
        "check_type":       l.check_type.value,
        "status":           l.status.value,
        "priority":         l.priority.value,
        "title":            l.title,
        "ata_chapter":      l.ata_chapter,
        "ata_description":  l.ata_description,
        "scheduled_start":  l.scheduled_start.isoformat() if l.scheduled_start else None,
        "scheduled_end":    l.scheduled_end.isoformat()   if l.scheduled_end   else None,
        "actual_start":     l.actual_start.isoformat()    if l.actual_start    else None,
        "actual_end":       l.actual_end.isoformat()      if l.actual_end      else None,
        "lead_technician":  l.lead_technician,
        "hangar_bay":       l.hangar_bay,
        "man_hours_est":    l.man_hours_est,
        "man_hours_actual": l.man_hours_actual,
        "parts_cost_usd":   l.parts_cost_usd,
        "labor_cost_usd":   l.labor_cost_usd,
        "work_order_ref":   l.work_order_ref,
        "ad_number":        l.ad_number,
        "findings":         l.findings,
        "approved_by":      l.approved_by,
        "sign_off_time":    l.sign_off_time.isoformat() if l.sign_off_time else None,
        "aircraft_reg":     l.aircraft.registration if l.aircraft else None,
    }


def _mel_summary(m: MELItem) -> dict:
    return {
        "id":              m.id,
        "mel_number":      m.mel_number,
        "ata_chapter":     m.ata_chapter,
        "description":     m.description,
        "category":        m.category,
        "dispatch_conditions": m.dispatch_conditions,
        "raised_date":     m.raised_date,
        "expiry_date":     m.expiry_date,
        "is_active":       m.is_active,
        "raised_by":       m.raised_by,
    }


def _aog_summary(g: AOGRecord) -> dict:
    return {
        "id":                   g.id,
        "aog_ref":              g.aog_ref,
        "status":               g.status.value,
        "location":             g.location,
        "fault_description":    g.fault_description,
        "ata_chapter":          g.ata_chapter,
        "grounded_at":          g.grounded_at.isoformat() if g.grounded_at else None,
        "cleared_at":           g.cleared_at.isoformat()  if g.cleared_at  else None,
        "affected_flights":     g.affected_flights,
        "parts_on_order":       g.parts_on_order,
        "go_team_dispatched":   g.go_team_dispatched,
        "estimated_tat":        g.estimated_tat,
        "notes":                g.notes,
        "aircraft_reg":         g.aircraft.registration if g.aircraft else None,
    }


@router.get("/tasks")
async def list_tasks(
    status:     Optional[str] = Query(None),
    priority:   Optional[str] = Query(None),
    check_type: Optional[str] = Query(None),
    db:         Session = Depends(get_db),
    _user:      User    = Depends(get_current_user),
):
    q = db.query(MaintenanceLog)
    if status:     q = q.filter(MaintenanceLog.status     == status)
    if priority:   q = q.filter(MaintenanceLog.priority   == priority)
    if check_type: q = q.filter(MaintenanceLog.check_type == check_type)
    logs = q.order_by(MaintenanceLog.priority.desc(), MaintenanceLog.scheduled_start).all()
    return {"total": len(logs), "tasks": [_log_summary(l) for l in logs]}


@router.get("/tasks/{task_id}")
async def get_task(task_id: int, db: Session = Depends(get_db), _u: User = Depends(get_current_user)):
    l = db.query(MaintenanceLog).filter(MaintenanceLog.id == task_id).first()
    if not l:
        raise HTTPException(status_code=404, detail="Maintenance task not found.")
    data = _log_summary(l)
    data.update({
        "description":        l.description,
        "technicians":        l.technicians,
        "parts_required":     l.parts_required,
        "corrective_action":  l.corrective_action,
        "sb_number":          l.sb_number,
        "license_number":     l.license_number,
        "next_due_hours":     l.next_due_hours,
        "next_due_date":      l.next_due_date,
    })
    return data


class TaskStatusUpdate(BaseModel):
    status:           Optional[str] = None
    findings:         Optional[str] = None
    corrective_action:Optional[str] = None
    man_hours_actual: Optional[float] = None
    approved_by:      Optional[str] = None
    license_number:   Optional[str] = None


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: int,
    body:    TaskStatusUpdate,
    db:      Session = Depends(get_db),
    _user:   User    = Depends(require_maintenance_chief),
):
    l = db.query(MaintenanceLog).filter(MaintenanceLog.id == task_id).first()
    if not l:
        raise HTTPException(status_code=404, detail="Task not found.")
    from datetime import datetime, timezone
    if body.status:
        l.status = MaintStatus(body.status)
        if body.status == "in_progress" and not l.actual_start:
            l.actual_start = datetime.now(timezone.utc)
        if body.status == "completed" and not l.actual_end:
            l.actual_end = datetime.now(timezone.utc)
    if body.findings          is not None: l.findings          = body.findings
    if body.corrective_action is not None: l.corrective_action = body.corrective_action
    if body.man_hours_actual  is not None: l.man_hours_actual  = body.man_hours_actual
    if body.approved_by       is not None: l.approved_by       = body.approved_by
    if body.license_number    is not None: l.license_number    = body.license_number
    db.commit()
    db.refresh(l)
    return _log_summary(l)


# ─── MEL Items ────────────────────────────────────────────────────────────

@router.get("/mel")
async def list_mel(db: Session = Depends(get_db), _u: User = Depends(get_current_user)):
    items = db.query(MELItem).filter(MELItem.is_active == True).all()
    return {"total": len(items), "mel_items": [_mel_summary(m) for m in items]}


# ─── AOG Records ──────────────────────────────────────────────────────────

@router.get("/aog")
async def list_aog(db: Session = Depends(get_db), _u: User = Depends(get_current_user)):
    records = db.query(AOGRecord).filter(AOGRecord.status != AOGStatus.CLEARED).all()
    return {"total": len(records), "aog_records": [_aog_summary(g) for g in records]}


# ─── Stats ────────────────────────────────────────────────────────────────

@router.get("/stats/summary")
async def maint_stats(db: Session = Depends(get_db), _u: User = Depends(get_current_user)):
    from sqlalchemy import func
    total_aircraft  = db.query(func.count(Aircraft.id)).scalar()
    aog_count       = db.query(func.count(Aircraft.id)).filter(Aircraft.is_aog == True).scalar()
    open_mel        = db.query(func.count(MELItem.id)).filter(MELItem.is_active == True).scalar()
    tasks_inprogress= db.query(func.count(MaintenanceLog.id)).filter(MaintenanceLog.status == MaintStatus.IN_PROGRESS).scalar()
    tasks_aog_prio  = db.query(func.count(MaintenanceLog.id)).filter(MaintenanceLog.priority == Priority.AOG).scalar()
    tasks_overdue   = db.query(func.count(MaintenanceLog.id)).filter(MaintenanceLog.status == MaintStatus.OVERDUE).scalar()

    return {
        "total_aircraft": total_aircraft,
        "aog_count": aog_count,
        "open_mel_items": open_mel,
        "tasks_in_progress": tasks_inprogress,
        "aog_priority_tasks": tasks_aog_prio,
        "overdue_tasks": tasks_overdue,
    }
