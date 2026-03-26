import json
import os
import urllib.request
from urllib.error import HTTPError, URLError

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8011/api")

EMPLOYEES = [
    {
        "name": "Rohan Mehta",
        "email": "rohan@company.com",
        "department": "Engineering",
        "role": "Backend Engineer",
        "skills": "Server, DB, API",
    },
    {
        "name": "Asha Patel",
        "email": "asha@company.com",
        "department": "IT",
        "role": "Support Engineer",
        "skills": "Access, Password, Networking",
    },
    {
        "name": "Neha Rao",
        "email": "neha@company.com",
        "department": "HR",
        "role": "HR Specialist",
        "skills": "Leave, Policy, Onboarding",
    },
    {
        "name": "Ishan Verma",
        "email": "ishan@company.com",
        "department": "Finance",
        "role": "Payroll Analyst",
        "skills": "Billing, Payroll, Reimbursement",
    },
]

TICKETS = [
    {
        "title": "Password reset needed",
        "description": "Locked out of account after too many attempts. Please reset.",
    },
    {
        "title": "Production server down",
        "description": "API is timing out across regions. High priority outage.",
    },
    {
        "title": "Leave policy question",
        "description": "Where can I find the latest HR leave policy?",
    },
]


def post_json(path: str, payload: dict):
    url = f"{API_BASE}{path}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def seed():
    print(f"Seeding API at {API_BASE}")
    for emp in EMPLOYEES:
        try:
            post_json("/employees", emp)
            print(f"Added employee: {emp['name']}")
        except HTTPError as e:
            if e.code == 400:
                print(f"Skipping employee (already exists?): {emp['email']}")
            else:
                raise

    for ticket in TICKETS:
        post_json("/tickets", ticket)
        print(f"Created ticket: {ticket['title']}")


if __name__ == "__main__":
    try:
        seed()
        print("Seed complete.")
    except URLError as e:
        print("Failed to reach API. Is the backend running?")
        raise
