import requests

# Add sample employees
employees = [
    {
        "name": "Alice Johnson",
        "email": "alice@company.com",
        "department": "Engineering",
        "role": "Senior Developer",
        "skills": "Database, Backend, Python"
    },
    {
        "name": "Bob Smith",
        "email": "bob@company.com",
        "department": "IT",
        "role": "IT Support",
        "skills": "Networking, Access, Hardware"
    },
    {
        "name": "Charlie Brown",
        "email": "charlie@company.com",
        "department": "HR",
        "role": "HR Manager",
        "skills": "HR, Leave, Onboarding"
    }
]

for emp in employees:
    response = requests.post('http://localhost:8001/api/employees', json=emp)
    print(f"Added {emp['name']}: {response.status_code}")

# Test ticket again
response = requests.post('http://localhost:8001/api/tickets', json={
    'title': 'Password reset',
    'description': 'I forgot my password and need to reset it.'
})

print("Ticket response:")
print(response.json())