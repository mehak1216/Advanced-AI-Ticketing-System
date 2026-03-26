from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from database import get_db
from models import Ticket, Employee
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/summary")
def get_analytics_summary(db: Session = Depends(get_db)):
    try:
        total_tickets = db.query(Ticket).count()
        open_tickets = db.query(Ticket).filter(Ticket.status != "Closed").count()
        resolved_tickets = db.query(Ticket).filter(Ticket.status == "Resolved").count()
        auto_resolved = db.query(Ticket).filter(Ticket.auto_resolved == True).count()
        escalated = db.query(Ticket).filter(Ticket.status == "Escalated").count()

        # Department load
        dept_load_rows = db.query(Employee.department, func.count(Ticket.id))\
            .join(Ticket, Employee.id == Ticket.assignee_id)\
            .filter(Ticket.status != "Closed")\
            .group_by(Employee.department).all()
        dept_load = {str(k): int(v) for k, v in dept_load_rows}

        # Avg resolution time by dept
        avg_time_rows = db.query(
            Employee.department,
            func.avg((func.julianday(Ticket.resolved_at) - func.julianday(Ticket.created_at)) * 24.0)
        ).join(Ticket, Employee.id == Ticket.assignee_id).filter(Ticket.resolved_at != None).group_by(Employee.department).all()
        avg_time = {str(k): (float(v) if v is not None else 0.0) for k, v in avg_time_rows}

        # Top categories
        week_ago = datetime.utcnow() - timedelta(days=7)
        top_category_rows = db.query(Ticket.category, func.count(Ticket.id)) \
            .filter(Ticket.created_at >= week_ago) \
            .group_by(Ticket.category).order_by(func.count(Ticket.id).desc()).limit(5).all()
        top_categories = [[str(k), int(v)] for k, v in top_category_rows]

        # Auto-resolution success
        helpful_feedbacks = db.query(Ticket).filter(Ticket.auto_resolved == True, Ticket.feedback == "Yes").count()
        total_feedbacks = db.query(Ticket).filter(Ticket.auto_resolved == True, Ticket.feedback.in_(["Yes", "No"])).count()
        success_rate = (helpful_feedbacks / total_feedbacks * 100) if total_feedbacks > 0 else 0

        return {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "resolved_tickets": resolved_tickets,
            "auto_resolved": auto_resolved,
            "escalated": escalated,
            "department_load": dept_load,
            "avg_resolution_time_by_dept": avg_time,
            "top_categories": top_categories,
            "auto_resolution_success_rate": success_rate
        }
    except (SQLAlchemyError, Exception):
        return {
            "total_tickets": 0,
            "open_tickets": 0,
            "resolved_tickets": 0,
            "auto_resolved": 0,
            "escalated": 0,
            "department_load": {},
            "avg_resolution_time_by_dept": {},
            "top_categories": [],
            "auto_resolution_success_rate": 0
        }
