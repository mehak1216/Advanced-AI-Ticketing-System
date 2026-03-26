import streamlit as st
import requests
import json
from datetime import datetime

# Configure page
st.set_page_config(page_title="AI Ticketing System", layout="wide")

# API base URL
API_BASE = "http://localhost:8001/api"
DEPARTMENTS = ["Engineering", "Finance", "HR", "IT", "Product", "Marketing", "Legal"]
STATUSES = ["New", "Assigned", "In Progress", "Pending Info", "Resolved", "Closed", "Escalated"]

st.title("🎫 AI Ticketing System")
st.markdown("---")

def get_employees():
    try:
        res = requests.get(f"{API_BASE}/employees", timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception:
        return []
    return []

def get_employee_name(emp_id, employees):
    for e in employees:
        if e["id"] == emp_id:
            return e["name"]
    return "Unassigned"

# Sidebar navigation
page = st.sidebar.radio("Navigation", ["Create Ticket", "View Tickets", "Employees", "Analytics"])

# ============ CREATE TICKET PAGE ============
if page == "Create Ticket":
    st.header("Submit a New Ticket")
    
    with st.form("ticket_form"):
        title = st.text_input("Ticket Title", placeholder="e.g., Password reset needed")
        description = st.text_area("Description", placeholder="Describe your issue...", height=150)
        submit_btn = st.form_submit_button("Submit Ticket")
        
        if submit_btn:
            if title and description:
                try:
                    response = requests.post(
                        f"{API_BASE}/tickets",
                        json={"title": title, "description": description},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        ticket = response.json()
                        st.success("✅ Ticket Created Successfully!")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Ticket ID", ticket["id"])
                        with col2:
                            st.metric("Category", ticket["category"])
                        with col3:
                            st.metric("Status", ticket["status"])
                        
                        st.subheader("AI Analysis")
                        analysis_col1, analysis_col2 = st.columns(2)
                        with analysis_col1:
                            st.write(f"**Summary**: {ticket['ai_summary']}")
                            st.write(f"**Severity**: {ticket['severity']}")
                            st.write(f"**Sentiment**: {ticket['sentiment']}")
                        with analysis_col2:
                            st.write(f"**Resolution Path**: {ticket['resolution_path']}")
                            st.write(f"**Confidence**: {ticket['confidence']:.1%}")
                            st.write(f"**Est. Time**: {ticket['estimated_resolution_time']} hours")
                        
                        if ticket["auto_resolved"]:
                            st.info(f"🤖 **Auto-Resolved**: {ticket['auto_response']}")
                        elif ticket["assignee_id"]:
                            st.info(f"✋ **Assigned to**: Department {ticket['suggested_department']}")
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
            else:
                st.warning("Please fill in both title and description")

# ============ VIEW TICKETS PAGE ============
elif page == "View Tickets":
    st.header("All Tickets")

    try:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["All"] + STATUSES)
        with col2:
            severity_filter = st.selectbox("Filter by Severity", ["All", "Critical", "High", "Medium", "Low"])
        with col3:
            dept_filter = st.selectbox("Filter by Department", ["All"] + DEPARTMENTS)
        with col4:
            sort_by = st.selectbox("Sort by", ["created_at", "severity", "status"])

        col5, col6 = st.columns(2)
        with col5:
            date_from = st.date_input("From date", value=None)
        with col6:
            date_to = st.date_input("To date", value=None)

        params = {}
        if status_filter != "All":
            params["status"] = status_filter
        if severity_filter != "All":
            params["severity"] = severity_filter
        if dept_filter != "All":
            params["department"] = dept_filter
        if date_from:
            params["date_from"] = datetime.combine(date_from, datetime.min.time()).isoformat()
        if date_to:
            params["date_to"] = datetime.combine(date_to, datetime.max.time()).isoformat()
        params["sort_by"] = sort_by
        params["sort_dir"] = "desc"

        response = requests.get(f"{API_BASE}/tickets", params=params, timeout=10)
        if response.status_code == 200:
            tickets = response.json()

            if tickets:
                auto_filter = st.selectbox("Filter by Type", ["All", "Auto-Resolved", "Manual"])

                filtered_tickets = tickets
                if auto_filter == "Auto-Resolved":
                    filtered_tickets = [t for t in filtered_tickets if t["auto_resolved"]]
                elif auto_filter == "Manual":
                    filtered_tickets = [t for t in filtered_tickets if not t["auto_resolved"]]

                st.write(f"Showing {len(filtered_tickets)} of {len(tickets)} tickets")

                employees = get_employees()

                for ticket in filtered_tickets:
                    with st.expander(f"#{ticket['id']} | {ticket['title']} | {ticket['status']}"):
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.write(f"**Category**: {ticket['category']}")
                        with col2:
                            st.write(f"**Severity**: {ticket['severity']}")
                        with col3:
                            st.write(f"**Status**: {ticket['status']}")
                        with col4:
                            st.write(f"**Created**: {ticket['created_at']}")

                        st.write(f"**Description**: {ticket['description']}")
                        st.write(f"**AI Summary**: {ticket['ai_summary']}")
                        st.write(f"**Department**: {ticket.get('suggested_department')}")
                        st.write(f"**Assignee**: {get_employee_name(ticket.get('assignee_id'), employees)}")

                        if ticket["auto_resolved"]:
                            st.success(f"✅ Auto-Resolved: {ticket['auto_response']}")
                            if ticket["feedback"] is None:
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("👍 Helpful", key=f"yes_{ticket['id']}"):
                                        requests.put(
                                            f"{API_BASE}/tickets/{ticket['id']}/feedback",
                                            params={"feedback": "Yes"}
                                        )
                                        st.success("Feedback recorded!")
                                with col2:
                                    if st.button("👎 Not Helpful", key=f"no_{ticket['id']}"):
                                        requests.put(
                                            f"{API_BASE}/tickets/{ticket['id']}/feedback",
                                            params={"feedback": "No"}
                                        )
                                        st.success("Feedback recorded!")

                        st.markdown("**Actions**")
                        action_col1, action_col2 = st.columns(2)
                        with action_col1:
                            new_status = st.selectbox(
                                "Update Status",
                                STATUSES,
                                index=STATUSES.index(ticket["status"]) if ticket["status"] in STATUSES else 0,
                                key=f"status_{ticket['id']}"
                            )
                        with action_col2:
                            assignee_options = ["Unassigned"] + [f"{e['id']}: {e['name']}" for e in employees]
                            selected_assignee = st.selectbox(
                                "Assign To",
                                assignee_options,
                                index=0,
                                key=f"assignee_{ticket['id']}"
                            )

                        if st.button("Apply Updates", key=f"apply_{ticket['id']}"):
                            payload = {"status": new_status}
                            if selected_assignee != "Unassigned":
                                payload["assignee_id"] = int(selected_assignee.split(":")[0])
                            requests.put(f"{API_BASE}/tickets/{ticket['id']}", json=payload)
                            st.success("Ticket updated.")

                        note = st.text_area("Internal Note", key=f"note_{ticket['id']}")
                        if st.button("Add Note", key=f"note_btn_{ticket['id']}"):
                            if note.strip():
                                requests.post(
                                    f"{API_BASE}/tickets/{ticket['id']}/notes",
                                    json={"message": note, "actor": "assignee"}
                                )
                                st.success("Note added.")

                        req_info = st.text_area("Request More Info", key=f"req_{ticket['id']}")
                        if st.button("Request Info", key=f"req_btn_{ticket['id']}"):
                            if req_info.strip():
                                requests.post(
                                    f"{API_BASE}/tickets/{ticket['id']}/request-info",
                                    json={"message": req_info, "actor": "assignee"}
                                )
                                st.info("Info request sent and status set to Pending Info.")

                        if st.checkbox("Show Timeline", key=f"timeline_{ticket['id']}"):
                            timeline_res = requests.get(f"{API_BASE}/tickets/{ticket['id']}/timeline")
                            if timeline_res.status_code == 200:
                                for ev in timeline_res.json():
                                    st.write(f"[{ev['created_at']}] {ev['event_type']} ({ev['actor']}): {ev['message']}")
            else:
                st.info("No tickets yet. Create one to get started!")
    except Exception as e:
        st.error(f"Error fetching tickets: {str(e)}")

# ============ EMPLOYEES PAGE ============
elif page == "Employees":
    st.header("Employee Directory")
    
    tab1, tab2 = st.tabs(["View Employees", "Add Employee"])
    
    with tab1:
        try:
            response = requests.get(f"{API_BASE}/employees", timeout=10)
            if response.status_code == 200:
                employees = response.json()
                
                if employees:
                    for emp in employees:
                        with st.expander(f"{emp['name']} | {emp['role']} | {emp['department']}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Email**: {emp['email']}")
                                st.write(f"**Department**: {emp['department']}")
                                st.write(f"**Skills**: {emp['skills']}")
                            with col2:
                                st.write(f"**Current Load**: {emp['current_load']} tickets")
                                st.write(f"**Avg Resolution**: {emp['avg_resolution_time']:.1f} hours")
                                st.write(f"**Status**: {emp['availability']}")
                else:
                    st.info("No employees yet. Add one below.")
        except Exception as e:
            st.error(f"Error fetching employees: {str(e)}")
    
    with tab2:
        st.subheader("Add New Employee")
        with st.form("emp_form"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            department = st.selectbox("Department", DEPARTMENTS)
            role = st.text_input("Role/Designation")
            skills = st.text_input("Skills (comma-separated)", placeholder="e.g., Database, Backend, Python")
            submit_emp = st.form_submit_button("Add Employee")
            
            if submit_emp:
                if name and email and role and skills:
                    try:
                        response = requests.post(
                            f"{API_BASE}/employees",
                            json={
                                "name": name,
                                "email": email,
                                "department": department,
                                "role": role,
                                "skills": skills
                            },
                            timeout=10
                        )
                        if response.status_code == 200:
                            st.success(f"✅ Employee {name} added!")
                        else:
                            st.error(f"Error: {response.text}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.warning("Please fill all fields")

# ============ ANALYTICS PAGE ============
elif page == "Analytics":
    st.header("📊 System Analytics")
    
    try:
        response = requests.get(f"{API_BASE}/analytics/summary", timeout=10)
        if response.status_code == 200:
            analytics = response.json()
            
            # Key Metrics
            st.subheader("Key Metrics")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Total Tickets", analytics.get("total_tickets", 0))
            with col2:
                st.metric("Open", analytics.get("open_tickets", 0))
            with col3:
                st.metric("Resolved", analytics.get("resolved_tickets", 0))
            with col4:
                st.metric("Auto-Resolved", analytics.get("auto_resolved", 0))
            with col5:
                st.metric("Escalated", analytics.get("escalated", 0))
            
            # Auto-resolution success rate
            success_rate = analytics.get("auto_resolution_success_rate", 0)
            st.metric(
                "Auto-Resolution Success Rate",
                f"{success_rate:.1f}%",
                delta="Helpful feedback ratio"
            )
            
            # Department Load
            st.subheader("Department Load")
            dept_load = analytics.get("department_load", {})
            if dept_load:
                st.bar_chart({k: v for k, v in dict(dept_load).items()})
            else:
                st.info("No department data yet")
            
            # Top Categories
            st.subheader("Top Ticket Categories")
            top_cats = analytics.get("top_categories", [])
            if top_cats:
                cat_data = {cat[0]: cat[1] for cat in top_cats}
                st.bar_chart(cat_data)
            else:
                st.info("No category data yet")
                
    except Exception as e:
        st.error(f"Error fetching analytics: {str(e)}")

st.markdown("---")
st.caption("Backend running on http://localhost:8001")
