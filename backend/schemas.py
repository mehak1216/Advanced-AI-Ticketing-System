from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TicketCreate(BaseModel):
    title: str
    description: str

class TicketUpdate(BaseModel):
    status: Optional[str] = None
    assignee_id: Optional[int] = None
    feedback: Optional[str] = None

class TicketNoteCreate(BaseModel):
    message: str
    actor: Optional[str] = "assignee"

class TicketRequestInfo(BaseModel):
    message: str
    actor: Optional[str] = "assignee"

class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    ai_summary: str
    severity: str
    sentiment: str
    resolution_path: str
    suggested_department: Optional[str]
    suggested_employee_id: Optional[int]
    confidence: float
    estimated_resolution_time: float
    status: str
    assignee_id: Optional[int]
    auto_resolved: bool
    auto_response: Optional[str]
    feedback: Optional[str]
    assigned_at: Optional[datetime]
    picked_up_at: Optional[datetime]
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class EmployeeCreate(BaseModel):
    name: str
    email: str
    department: str
    role: str
    skills: str

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    skills: Optional[str] = None
    availability: Optional[str] = None
    active: Optional[bool] = None

class EmployeeResponse(BaseModel):
    id: int
    name: str
    email: str
    department: str
    role: str
    skills: str
    avg_resolution_time: float
    current_load: int
    availability: str
    active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class TicketEventResponse(BaseModel):
    id: int
    ticket_id: int
    event_type: str
    message: str
    actor: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
