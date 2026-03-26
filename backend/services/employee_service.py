from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Employee, Ticket
from typing import List, Optional

def suggest_assignee(db: Session, department: str, category: str, severity: str, exclude_id: Optional[int] = None) -> Employee:
    # Filter by department
    employees = db.query(Employee).filter(
        Employee.department == department,
        Employee.active == True,
        Employee.availability == "Available"
    ).all()

    if not employees:
        return None

    if exclude_id is not None:
        employees = [e for e in employees if e.id != exclude_id]
        if not employees:
            return None

    # Score based on skills match, load, avg time
    def score_employee(emp: Employee):
        skill_match = 1 if category.lower() in emp.skills.lower() else 0
        load_penalty = emp.current_load * 0.1
        time_bonus = 1 / (emp.avg_resolution_time + 1)  # lower time better
        return skill_match + time_bonus - load_penalty

    employees.sort(key=score_employee, reverse=True)
    return employees[0] if employees else None

def update_employee_load(db: Session, employee_id: int, increment: bool):
    emp = db.query(Employee).get(employee_id)
    if emp:
        emp.current_load += 1 if increment else -1
        if emp.current_load < 0:
            emp.current_load = 0
        db.commit()

def recalc_avg_resolution_time(db: Session, employee_id: int):
    avg_time = db.query(
        func.avg((func.julianday(Ticket.resolved_at) - func.julianday(Ticket.created_at)) * 24.0)
    ).filter(
        Ticket.assignee_id == employee_id,
        Ticket.resolved_at != None
    ).scalar()
    emp = db.query(Employee).get(employee_id)
    if emp:
        emp.avg_resolution_time = float(avg_time) if avg_time is not None else 0.0
        db.commit()
