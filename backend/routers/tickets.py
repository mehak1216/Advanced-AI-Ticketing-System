from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Ticket, Employee, TicketEvent
from schemas import TicketCreate, TicketUpdate, TicketResponse, TicketNoteCreate, TicketRequestInfo, TicketEventResponse
from services.ai_service import analyze_ticket, generate_auto_response
from services.employee_service import suggest_assignee, update_employee_load, recalc_avg_resolution_time
from typing import List
from datetime import datetime, timedelta
from services.ws_service import broadcast_event

router = APIRouter()

def add_event(db: Session, ticket_id: int, event_type: str, message: str, actor: str = "system"):
    event = TicketEvent(
        ticket_id=ticket_id,
        event_type=event_type,
        message=message,
        actor=actor
    )
    db.add(event)
    db.commit()

def run_escalations(db: Session):
    cutoff = datetime.utcnow() - timedelta(hours=2)
    candidates = db.query(Ticket).filter(
        Ticket.status == "Assigned",
        Ticket.severity.in_(["High", "Critical"]),
        Ticket.assigned_at != None,
        Ticket.assigned_at < cutoff
    ).all()

    for ticket in candidates:
        if not ticket.suggested_department:
            continue
        new_assignee = suggest_assignee(
            db,
            ticket.suggested_department,
            ticket.category,
            ticket.severity,
            exclude_id=ticket.assignee_id
        )
        if not new_assignee:
            continue

        if ticket.assignee_id:
            update_employee_load(db, ticket.assignee_id, False)
        ticket.assignee_id = new_assignee.id
        ticket.suggested_employee_id = new_assignee.id
        ticket.status = "Escalated"
        ticket.assigned_at = datetime.utcnow()
        update_employee_load(db, new_assignee.id, True)
        db.commit()
        add_event(db, ticket.id, "escalation", f"Ticket escalated and reassigned to {new_assignee.name}.", "system")

def apply_priority_bump(category: str, severity: str) -> str:
    bump_map = {
        "DB": "Critical",
        "Server": "Critical",
        "Access": "High",
        "Legal": "High",
    }
    bumped = bump_map.get(category, severity)
    return bumped

@router.post("/", response_model=TicketResponse)
def create_ticket(ticket: TicketCreate, db: Session = Depends(get_db)):
    # Analyze with AI
    analysis = analyze_ticket(ticket.title, ticket.description)
    analysis.severity = apply_priority_bump(analysis.category, analysis.severity)

    # Create ticket
    db_ticket = Ticket(
        title=ticket.title,
        description=ticket.description,
        category=analysis.category,
        ai_summary=analysis.ai_summary,
        severity=analysis.severity,
        sentiment=analysis.sentiment,
        resolution_path=analysis.resolution_path,
        suggested_department=analysis.suggested_department,
        confidence=analysis.confidence,
        estimated_resolution_time=analysis.estimated_resolution_time
    )

    if analysis.resolution_path == "Auto-resolve":
        db_ticket.auto_resolved = True
        db_ticket.auto_response = generate_auto_response(analysis.dict())
        db_ticket.status = "Resolved"
        db_ticket.resolved_at = datetime.utcnow()
    else:
        # Suggest assignee
        assignee = suggest_assignee(db, analysis.suggested_department, analysis.category, analysis.severity)
        if assignee:
            db_ticket.suggested_employee_id = assignee.id
            db_ticket.assignee_id = assignee.id
            db_ticket.status = "Assigned"
            db_ticket.assigned_at = datetime.utcnow()
            update_employee_load(db, assignee.id, True)

    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    add_event(db, db_ticket.id, "created", "Ticket created.", "user")
    if db_ticket.auto_resolved:
        add_event(db, db_ticket.id, "status_change", "Ticket auto-resolved.", "system")
    elif db_ticket.assignee_id:
        add_event(db, db_ticket.id, "assignment", "Ticket assigned to assignee.", "system")
    try:
        awaitable = broadcast_event({"type": "ticket_created", "ticket_id": db_ticket.id})
        if awaitable:
            import asyncio
            asyncio.create_task(awaitable)
    except Exception:
        pass
    return db_ticket

@router.get("/", response_model=List[TicketResponse])
def get_tickets(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    department: str = None,
    severity: str = None,
    date_from: str = None,
    date_to: str = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    db: Session = Depends(get_db)
):
    run_escalations(db)
    query = db.query(Ticket)

    if status:
        query = query.filter(Ticket.status == status)
    if department:
        query = query.filter(Ticket.suggested_department == department)
    if severity:
        query = query.filter(Ticket.severity == severity)
    if date_from:
        try:
            df = datetime.fromisoformat(date_from)
            query = query.filter(Ticket.created_at >= df)
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to)
            query = query.filter(Ticket.created_at <= dt)
        except ValueError:
            pass

    sort_col = getattr(Ticket, sort_by, Ticket.created_at)
    if sort_dir.lower() == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    tickets = query.offset(skip).limit(limit).all()
    return tickets

@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@router.put("/{ticket_id}", response_model=TicketResponse)
def update_ticket(ticket_id: int, ticket_update: TicketUpdate, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    original_status = ticket.status
    original_assignee = ticket.assignee_id

    for key, value in ticket_update.dict(exclude_unset=True).items():
        setattr(ticket, key, value)

    if ticket_update.assignee_id and ticket_update.assignee_id != original_assignee:
        if original_assignee:
            update_employee_load(db, original_assignee, False)
        update_employee_load(db, ticket_update.assignee_id, True)
        ticket.assigned_at = datetime.utcnow()
        add_event(db, ticket.id, "assignment", f"Ticket assigned to employee {ticket_update.assignee_id}.", "system")

    if ticket_update.status == "In Progress" and ticket.picked_up_at is None:
        ticket.picked_up_at = datetime.utcnow()

    if ticket_update.status in ["Resolved", "Closed"] and ticket.resolved_at is None:
        ticket.resolved_at = datetime.utcnow()
        if ticket.assignee_id:
            update_employee_load(db, ticket.assignee_id, False)
            recalc_avg_resolution_time(db, ticket.assignee_id)

    if ticket_update.status and ticket_update.status != original_status:
        add_event(db, ticket.id, "status_change", f"Status changed from {original_status} to {ticket_update.status}.", "assignee")

    if ticket_update.feedback:
        add_event(db, ticket.id, "note", f"Feedback: {ticket_update.feedback}.", "user")

    db.commit()
    db.refresh(ticket)

    try:
        awaitable = broadcast_event({"type": "ticket_updated", "ticket_id": ticket.id})
        if awaitable:
            import asyncio
            asyncio.create_task(awaitable)
    except Exception:
        pass

    return ticket

@router.post("/{ticket_id}/notes", response_model=TicketEventResponse)
def add_note(ticket_id: int, note: TicketNoteCreate, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    event = TicketEvent(
        ticket_id=ticket_id,
        event_type="note",
        message=note.message,
        actor=note.actor or "assignee"
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    try:
        awaitable = broadcast_event({"type": "ticket_note", "ticket_id": ticket_id})
        if awaitable:
            import asyncio
            asyncio.create_task(awaitable)
    except Exception:
        pass
    return event

@router.post("/{ticket_id}/request-info", response_model=TicketEventResponse)
def request_info(ticket_id: int, payload: TicketRequestInfo, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = "Pending Info"
    event = TicketEvent(
        ticket_id=ticket_id,
        event_type="request_info",
        message=payload.message,
        actor=payload.actor or "assignee"
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    add_event(db, ticket_id, "notification", "User notified: more information requested.", "system")
    try:
        awaitable = broadcast_event({"type": "ticket_request_info", "ticket_id": ticket_id})
        if awaitable:
            import asyncio
            asyncio.create_task(awaitable)
    except Exception:
        pass
    return event

@router.get("/{ticket_id}/timeline", response_model=List[TicketEventResponse])
def get_timeline(ticket_id: int, db: Session = Depends(get_db)):
    events = db.query(TicketEvent).filter(TicketEvent.ticket_id == ticket_id).order_by(TicketEvent.created_at.asc()).all()
    return events

@router.put("/{ticket_id}/feedback")
def submit_feedback(ticket_id: int, feedback: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.feedback = feedback
    db.commit()
    add_event(db, ticket_id, "note", f"Feedback: {feedback}.", "user")
    try:
        awaitable = broadcast_event({"type": "ticket_feedback", "ticket_id": ticket_id})
        if awaitable:
            import asyncio
            asyncio.create_task(awaitable)
    except Exception:
        pass
    return {"message": "Feedback submitted"}
