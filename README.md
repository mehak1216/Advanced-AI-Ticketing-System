# Advanced AI Ticketing System

A full-stack AI-powered internal ticketing platform that analyzes tickets, auto-resolves common issues, routes to the right department and assignee, tracks lifecycle events, and provides analytics with real-time updates.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite, OpenAI GPT-4o-mini
- **Frontend**: Next.js, React, TailwindCSS
- **AI**: OpenAI for ticket analysis and auto-resolution

## Features

### Core Modules

1. **Ticket Intake & AI Analysis**
   - AI analyzes tickets and produces structured output
   - Categorizes tickets (Billing, Bug, Access, HR, Server, DB, Feature, Other)
   - Determines severity, sentiment, resolution path

2. **Auto-Resolution Engine**
   - Auto-resolves simple issues like password resets, FAQs
   - Generates professional responses with feedback options

3. **Intelligent Department Routing**
   - Routes tickets to correct departments based on category
   - Priority bumping for critical issues

4. **Employee Directory & Assignee Suggestion**
   - Maintains employee database with skills, load, availability
   - Suggests best assignee based on skill match, load, and availability

5. **Ticket Lifecycle Management**
   - Full ticket statuses: New → Assigned → In Progress → Pending Info → Resolved → Closed
   - Assignee updates, internal notes, escalation
   - Timeline history and simulated notifications
   - Search, filter, and sort tickets by status, department, severity, and date

6. **Analytics Dashboard**
   - Ticket counts, department load, resolution times
   - Top recurring categories, auto-resolution success rate

### Bonus
- Real-time ticket updates without page refresh (WebSocket)

## Submission Checklist (from PDF)

- Public GitHub repo with clean commits
- README with overview, tech stack, setup, feature list, known limitations, screenshots/GIFs
- Demo video (max 5 minutes) covering:
  - Introduction (problem + solution)
  - Full UI walkthrough (every screen + flow)
  - AI in action with at least 3 scenarios
  - One key prompt design decision
  - One limitation + how you would fix it
- Submission form with name, GitHub link, video link, 100-word reflection

## Final Submission Checklist

### Code & Features
- Module 1: Ticket Intake & AI Analysis
- Module 2: Auto-resolution Engine
- Module 3: Department Routing + Priority Bump
- Module 4: Employee Directory & Assignee Suggestion
- Module 5: Ticket Lifecycle + Timeline + Escalation
- Module 6: Analytics Dashboard
- Bonus: Real-time updates (WebSocket)

### Repo Requirements
- Public GitHub repo with clean commits
- README includes overview, tech stack, setup, features, limitations, screenshots/GIFs

### Demo Video (Max 5 min)
- Introduction (problem + solution)
- UI walkthrough (all screens/flows)
- AI in action (3 scenarios)
- Prompt design decision explanation
- One limitation + fix idea

### Submission Form
- Name
- GitHub link
- Video link
- 100-word reflection

## Screenshots / GIFs

Add screenshots or GIFs here for the final submission.

### Suggested Captures
- Dashboard overview (System Health + Analytics)
- Create Ticket flow (AI analysis + auto-resolve)
- Ticket lifecycle actions (status update, notes, request info)
- Timeline view with events

## Setup Instructions

### Backend

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

4. Run the server:
   ```bash
   python -m uvicorn main:app --reload --port 8011
   ```

   If you already have an old `ticketing.db`, delete it to apply the new schema:
   ```bash
   # PowerShell
   Remove-Item backend\\ticketing.db
   ```

### Frontend

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

4. Open http://localhost:3000 or 3001/3004 if that port is in use.

## API Documentation

Once the backend is running, visit http://127.0.0.1:8011/docs for interactive API documentation.

## Demo

[Link to demo video]

## Known Limitations

- Currently uses SQLite for simplicity; production should use PostgreSQL
- AI analysis depends on OpenAI API availability
- Email notifications are simulated

## Future Improvements

- Add user authentication and roles
- Integrate with actual email systems
- Add richer analytics charts
