import os
import json
from openai import OpenAI
from pydantic import BaseModel
from typing import Optional

# Mock if no API key
if not os.getenv("OPENAI_API_KEY"):
    class MockCompletions:
        @staticmethod
        def create(**kwargs):
            class MockResponse:
                class MockChoice:
                    class MockMessage:
                        content = '{"category": "Access", "ai_summary": "User needs password reset.", "severity": "Low", "sentiment": "Neutral", "resolution_path": "Auto-resolve", "confidence": 0.95, "estimated_resolution_time": 0.5}'
                    message = MockMessage()
                choices = [MockChoice()]
            return MockResponse()
    class MockChat:
        completions = MockCompletions()
    class MockClient:
        chat = MockChat()
    client = MockClient()
else:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class AIAnalysis(BaseModel):
    category: str  # Billing, Bug, Access, HR, Server, DB, Feature, Other
    ai_summary: str
    severity: str  # Critical, High, Medium, Low
    sentiment: str  # Frustrated, Neutral, Polite
    resolution_path: str  # Auto-resolve or Assign to department
    suggested_department: Optional[str] = None
    suggested_employee_name: Optional[str] = None
    confidence: float
    estimated_resolution_time: float  # in hours

def analyze_ticket(title: str, description: str) -> AIAnalysis:
    prompt = f"""
Analyze the following ticket and provide a structured response.

Ticket Title: {title}
Ticket Description: {description}

Output in JSON format with the following fields:
- category: One of Billing, Bug, Access, HR, Server, DB, Feature, Other
- ai_summary: 2-3 sentences summarizing the issue
- severity: Critical, High, Medium, Low
- sentiment: Frustrated, Neutral, Polite
  - resolution_path: "Auto-resolve" if it can be resolved automatically, otherwise "Assign to department"
  - suggested_department: If resolution_path is "Assign to department", suggest the department (e.g., Engineering, Finance, HR, IT, Product, Marketing, Legal)
  - suggested_employee_name: If resolution_path is "Assign to department", suggest a best-fit employee name or "Unknown"
  - confidence: A float between 0 and 1 representing confidence in the analysis
  - estimated_resolution_time: Estimated time in hours to resolve

Examples of auto-resolvable:
- Password reset
- How to apply for leave
- General FAQs
- Status updates
- Simple billing clarifications

For routing:
- Database/Server issues -> Engineering
- Payroll/Salary -> Finance
- Leave/HR -> HR
- Access -> IT
- Bugs/Features -> Product/Engineering
- Marketing -> Marketing
- Legal -> Legal
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an AI assistant for ticket analysis. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=500
    )

    content = response.choices[0].message.content
    try:
        data = json.loads(content)
        return AIAnalysis(**data)
    except:
        # Fallback
        return AIAnalysis(
            category="Other",
            ai_summary="Unable to analyze",
            severity="Medium",
            sentiment="Neutral",
            resolution_path="Assign to department",
            suggested_department="IT",
            confidence=0.5,
            estimated_resolution_time=2.0
        )

def generate_auto_response(ticket: dict) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        return "Thank you for your report. Our team will look into this bug. Was this helpful? Yes / No"
    
    prompt = f"""
Generate a professional auto-response for the following ticket.

Category: {ticket['category']}
Summary: {ticket['ai_summary']}
Severity: {ticket['severity']}
Sentiment: {ticket['sentiment']}

The response should:
- Be professional and helpful
- Reference the specific issue
- Include a feedback option: "Was this helpful? Yes / No"

Keep it concise.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a customer support AI. Generate helpful responses."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=300
    )

    return response.choices[0].message.content
