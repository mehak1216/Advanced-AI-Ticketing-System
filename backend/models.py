from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    department = Column(String)
    role = Column(String)
    skills = Column(Text)  # JSON string of skills
    avg_resolution_time = Column(Float, default=0.0)  # in hours
    current_load = Column(Integer, default=0)
    availability = Column(String, default="Available")  # Available, Busy, On Leave
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    category = Column(String)  # Billing, Bug, etc.
    ai_summary = Column(Text)
    severity = Column(String)  # Critical, High, etc.
    sentiment = Column(String)  # Frustrated, Neutral, Polite
    resolution_path = Column(String)  # Auto-resolve or Assign
    suggested_department = Column(String)
    suggested_employee_id = Column(Integer, ForeignKey("employees.id"))
    confidence = Column(Float)
    estimated_resolution_time = Column(Float)  # in hours
    status = Column(String, default="New")  # New, Assigned, In Progress, Pending Info, Resolved, Closed
    assignee_id = Column(Integer, ForeignKey("employees.id"))
    auto_resolved = Column(Boolean, default=False)
    auto_response = Column(Text)
    feedback = Column(String)  # Yes, No, None
    assigned_at = Column(DateTime(timezone=True))
    picked_up_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    suggested_employee = relationship("Employee", foreign_keys=[suggested_employee_id])
    assignee = relationship("Employee", foreign_keys=[assignee_id])
    events = relationship("TicketEvent", back_populates="ticket", cascade="all, delete-orphan")

class TicketEvent(Base):
    __tablename__ = "ticket_events"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), index=True)
    event_type = Column(String)  # created, status_change, assignment, note, request_info, notification, escalation
    message = Column(Text)
    actor = Column(String)  # system, user, assignee, admin
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ticket = relationship("Ticket", back_populates="events")
