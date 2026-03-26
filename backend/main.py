from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, ensure_schema
from models import Base
from routers import tickets, employees, analytics, ws

ensure_schema()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Ticketing System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickets.router, prefix="/api/tickets", tags=["tickets"])
app.include_router(employees.router, prefix="/api/employees", tags=["employees"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(ws.router, prefix="/api/ws", tags=["ws"])

@app.get("/")
def read_root():
    return {"message": "AI Ticketing System API"}
