from database import create_tables
from authentication import AuthManager
from department_manager import DepartmentManager
department_manager = DepartmentManager()
auth_manager = AuthManager.get_instance()
create_tables()
auth_manager.create_default_admin()
department_manager.create_default_department()
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, FileResponse  
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Optional
from pdf_report import PDFReportGenerator
from pdf_payslip import PDFPayslipGenerator
from attendance import AttendanceManager
from notification import NotificationManager, InAppNotifier
from payroll import PayrollManager, ConcreteStrategyA
from logger import Logger
from datetime import datetime
app = FastAPI()
logger = Logger.get_instance()
pdf_generator = PDFReportGenerator()
pdf_payslip_generator = PDFPayslipGenerator()
attendance_manager = AttendanceManager()
notification_manager = NotificationManager()

inapp_notifier = InAppNotifier(notification_manager.subject) 
payroll_manager = PayrollManager(strategy=ConcreteStrategyA(), notifier=notification_manager)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ----------------------
# Dashboard
# ----------------------
@app.get("/", response_class=HTMLResponse)
async def home():
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    token = request.cookies.get("session_token")
    if token and auth_manager.validate_token(token):
        username = auth_manager.get_logged_in_user(token)
        role = auth_manager.get_user_role(token)

        # Load user's notifications
        notifications = [
            n for n in inapp_notifier.notifications if n["to"] == username
        ][::-1]  # latest first

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "username": username,
            "role": role,
            "notifications": notifications
        })
    return RedirectResponse(url="/login")


# ----------------------
# Authentication
# ----------------------
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    
    return templates.TemplateResponse("login.html", {"request": request, "username": None})


@app.post("/login")
async def login_user(request: Request, username: str = Form(...), password: str = Form(...)):
    success, result = auth_manager.login(username, password)
    if not success:
        logger.log_event(username, "Login Failed", {"reason": "Invalid credentials"})
        return templates.TemplateResponse("login.html", {"request": request, "error": result, "username": None})
    logger.log_event(username, "Login Successful")
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="session_token", value=result, httponly=True)
    return response


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "username": None})


@app.post("/register")
async def register_user(request: Request,
                        username: str = Form(...),
                        password: str = Form(...)):   
    success, msg = auth_manager.register_user(username, password, "employee")  
    if not success:
        return templates.TemplateResponse("register.html", {"request": request, "error": msg, "username": None})
    
    # Log the registration attempt
    logger.log_event(username, "Registration Successful")  

    success, token = auth_manager.login(username, password)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="session_token", value=token, httponly=True)
    return response


@app.get("/logout")
async def logout(request: Request):
    token = request.cookies.get("session_token")
    if token:
        # Get username BEFORE logging out the session
        username = auth_manager.get_logged_in_user(token)
        # Log the event with the correct username
        logger.log_event(username, "Logged out")
        
        # Now, log out the session
        auth_manager.logout(token)
    
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session_token")
    return response

# ----------------------
# Attendance Routes
# ----------------------
@app.get("/attendance", response_class=HTMLResponse)
async def attendance_page(request: Request):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")

    username = auth_manager.get_logged_in_user(token)
    role = auth_manager.get_user_role(token)

     
    records = []
    total_hours = 0

    if role == 'admin': # Admin sees ALL records
        all_db_records = attendance_manager.get_all_attendance_records()
        for r in all_db_records:
            hours_worked_for_entry = 0
            if r.check_in and r.check_out:
                try:
                    in_time = datetime.strptime(r.check_in, "%H:%M:%S")
                    out_time = datetime.strptime(r.check_out, "%H:%M:%S")
                    delta = out_time - in_time
                    hours_worked_for_entry = round(delta.total_seconds() / 3600, 2)
                except ValueError:
                    hours_worked_for_entry = 0 
            records.append({
                "employee_id": r.employee_id,
                "date": r.date,
                "check_in": r.check_in or '-',
                "check_out": r.check_out or '-',
                "hours": hours_worked_for_entry
            })
        total_hours_dict = attendance_manager.get_total_hours_for_all_employees()
        total_hours = sum(total_hours_dict.values()) if total_hours_dict else 0
        
    elif role == 'manager': # Manager sees records for their department and sub-departments
        
        # Adjust this to use get_all_users and find the manager's department_id
        manager_user_obj = next((u for u in auth_manager.get_all_users() if u['username'] == username), None)
        manager_dept_id = manager_user_obj['department_id'] if manager_user_obj else None

        if manager_dept_id:
            # Get all relevant department IDs (manager's dept + its children)
            relevant_dept_ids = department_manager.get_all_department_ids_in_hierarchy(manager_dept_id)
            
            # Fetch users in these departments
            users_in_relevant_depts = auth_manager.get_users_by_department_ids(relevant_dept_ids)
            relevant_usernames = [u["username"] for u in users_in_relevant_depts]

            # Fetch attendance records for these users
            all_db_records = attendance_manager.get_attendance_for_employees(relevant_usernames)
            for r in all_db_records:
                hours_worked_for_entry = 0
                if r.check_in and r.check_out:
                    try:
                        in_time = datetime.strptime(r.check_in, "%H:%M:%S")
                        out_time = datetime.strptime(r.check_out, "%H:%M:%S")
                        delta = out_time - in_time
                        hours_worked_for_entry = round(delta.total_seconds() / 3600, 2)
                    except ValueError:
                        hours_worked_for_entry = 0 
                records.append({
                    "employee_id": r.employee_id,
                    "date": r.date,
                    "check_in": r.check_in or '-',
                    "check_out": r.check_out or '-',
                    "hours": hours_worked_for_entry
                })
            
            # Calculate total hours for relevant employees
            total_hours_dict = attendance_manager.get_total_hours_for_employees(relevant_usernames)
            total_hours = sum(total_hours_dict.values()) if total_hours_dict else 0
        else:
            # Manager not assigned to a department, show only their own records or a message
            records = attendance_manager.get_attendance_for_employee(username)
            for r in records:  
                hours_worked_for_entry = 0
                if r.get("check_in") and r.get("check_out"):
                    try:
                        in_time = datetime.strptime(r["check_in"], "%H:%M:%S")
                        out_time = datetime.strptime(r["check_out"], "%H:%M:%S")
                        delta = out_time - in_time
                        hours_worked_for_entry = round(delta.total_seconds() / 3600, 2)
                    except ValueError:
                        hours_worked_for_entry = 0
                r["hours"] = hours_worked_for_entry
            total_hours = attendance_manager.get_total_hours_for_employee(username)
            
    else: # Employee role
        records = attendance_manager.get_attendance_for_employee(username)
        for r in records:
            hours_worked_for_entry = 0
            if r.get("check_in") and r.get("check_out"):
                try:
                    in_time = datetime.strptime(r["check_in"], "%H:%M:%S")
                    out_time = datetime.strptime(r["check_out"], "%H:%M:%S")
                    delta = out_time - in_time
                    hours_worked_for_entry = round(delta.total_seconds() / 3600, 2)
                except ValueError:
                    hours_worked_for_entry = 0
            r["hours"] = hours_worked_for_entry
        total_hours = attendance_manager.get_total_hours_for_employee(username)

    return templates.TemplateResponse("attendance.html", {
        "request": request,
        "username": username,
        "role": role,
        "records": records,
        "total_hours": total_hours,
        "message": None
    })



@app.post("/attendance/checkin")
async def attendance_checkin(request: Request):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")

    username = auth_manager.get_logged_in_user(token)
    role = auth_manager.get_user_role(token)

    success, msg = attendance_manager.check_in(username)
    notification_manager.send_notification(msg, username)

    # Re-fetch data based on role, just like the GET route
    records = []
    total_hours = 0

    if role == 'admin': # Admin sees ALL records
        all_db_records = attendance_manager.get_all_attendance_records()
        for r in all_db_records:
            hours_worked_for_entry = 0
            if r.check_in and r.check_out:
                try:
                    in_time = datetime.strptime(r.check_in, "%H:%M:%S")
                    out_time = datetime.strptime(r.check_out, "%H:%M:%S")
                    delta = out_time - in_time
                    hours_worked_for_entry = round(delta.total_seconds() / 3600, 2)
                except ValueError:
                    hours_worked_for_entry = 0 
            records.append({
                "employee_id": r.employee_id,
                "date": r.date,
                "check_in": r.check_in or '-',
                "check_out": r.check_out or '-',
                "hours": hours_worked_for_entry
            })
        total_hours_dict = attendance_manager.get_total_hours_for_all_employees()
        total_hours = sum(total_hours_dict.values()) if total_hours_dict else 0

    elif role == 'manager': # Manager sees records for their department and sub-departments
        manager_user_obj = next((u for u in auth_manager.get_all_users() if u['username'] == username), None)
        manager_dept_id = manager_user_obj['department_id'] if manager_user_obj else None

        if manager_dept_id:
            relevant_dept_ids = department_manager.get_all_department_ids_in_hierarchy(manager_dept_id)
            users_in_relevant_depts = auth_manager.get_users_by_department_ids(relevant_dept_ids)
            relevant_usernames = [u["username"] for u in users_in_relevant_depts]

            all_db_records = attendance_manager.get_attendance_for_employees(relevant_usernames)
            for r in all_db_records:
                hours_worked_for_entry = 0
                if r.check_in and r.check_out:
                    try:
                        in_time = datetime.strptime(r.check_in, "%H:%M:%S")
                        out_time = datetime.strptime(r.check_out, "%H:%M:%S")
                        delta = out_time - in_time
                        hours_worked_for_entry = round(delta.total_seconds() / 3600, 2)
                    except ValueError:
                        hours_worked_for_entry = 0 
                records.append({
                    "employee_id": r.employee_id,
                    "date": r.date,
                    "check_in": r.check_in or '-',
                    "check_out": r.check_out or '-',
                    "hours": hours_worked_for_entry
                })

            total_hours_dict = attendance_manager.get_total_hours_for_employees(relevant_usernames)
            total_hours = sum(total_hours_dict.values()) if total_hours_dict else 0
        else:
            records = attendance_manager.get_attendance_for_employee(username)
            for r in records:
                hours_worked_for_entry = 0
                if r.get("check_in") and r.get("check_out"):
                    try:
                        in_time = datetime.strptime(r["check_in"], "%H:%M:%S")
                        out_time = datetime.strptime(r["check_out"], "%H:%M:%S")
                        delta = out_time - in_time
                        hours_worked_for_entry = round(delta.total_seconds() / 3600, 2)
                    except ValueError:
                        hours_worked_for_entry = 0
                r["hours"] = hours_worked_for_entry
            total_hours = attendance_manager.get_total_hours_for_employee(username)

    else: # Employee role
        records = attendance_manager.get_attendance_for_employee(username)
        for r in records:
            hours_worked_for_entry = 0
            if r.get("check_in") and r.get("check_out"):
                try:
                    in_time = datetime.strptime(r["check_in"], "%H:%M:%S")
                    out_time = datetime.strptime(r["check_out"], "%H:%M:%S")
                    delta = out_time - in_time
                    hours_worked_for_entry = round(delta.total_seconds() / 3600, 2)
                except ValueError:
                    hours_worked_for_entry = 0
            r["hours"] = hours_worked_for_entry
        total_hours = attendance_manager.get_total_hours_for_employee(username)

    return templates.TemplateResponse("attendance.html", {
        "request": request,
        "username": username,
        "role": role,
        "records": records,
        "total_hours": total_hours,
        "message": msg
    })

@app.post("/attendance/checkout")
async def attendance_checkout(request: Request):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")

    username = auth_manager.get_logged_in_user(token)
    role = auth_manager.get_user_role(token)

    success, msg = attendance_manager.check_out(username)
    notification_manager.send_notification(msg, username)

    # Re-fetch data based on role, just like the GET route
    records = []
    total_hours = 0

    if role == 'admin': # Admin sees ALL records
        all_db_records = attendance_manager.get_all_attendance_records()
        for r in all_db_records:
            hours_worked_for_entry = 0
            if r.check_in and r.check_out:
                try:
                    in_time = datetime.strptime(r.check_in, "%H:%M:%S")
                    out_time = datetime.strptime(r.check_out, "%H:%M:%S")
                    delta = out_time - in_time
                    hours_worked_for_entry = round(delta.total_seconds() / 3600, 2)
                except ValueError:
                    hours_worked_for_entry = 0 

            records.append({
                "employee_id": r.employee_id,
                "date": r.date,
                "check_in": r.check_in or '-',
                "check_out": r.check_out or '-',
                "hours": hours_worked_for_entry
            })
        total_hours_dict = attendance_manager.get_total_hours_for_all_employees()
        total_hours = sum(total_hours_dict.values()) if total_hours_dict else 0

    elif role == 'manager': # Manager sees records for their department and sub-departments
        manager_user_obj = next((u for u in auth_manager.get_all_users() if u['username'] == username), None)
        manager_dept_id = manager_user_obj['department_id'] if manager_user_obj else None

        if manager_dept_id:
            relevant_dept_ids = department_manager.get_all_department_ids_in_hierarchy(manager_dept_id)
            users_in_relevant_depts = auth_manager.get_users_by_department_ids(relevant_dept_ids)
            relevant_usernames = [u["username"] for u in users_in_relevant_depts]

            all_db_records = attendance_manager.get_attendance_for_employees(relevant_usernames)
            for r in all_db_records:
                hours_worked_for_entry = 0
                if r.check_in and r.check_out:
                    try:
                        in_time = datetime.strptime(r.check_in, "%H:%M:%S")
                        out_time = datetime.strptime(r.check_out, "%H:%M:%S")
                        delta = out_time - in_time
                        hours_worked_for_entry = round(delta.total_seconds() / 3600, 2)
                    except ValueError:
                        hours_worked_for_entry = 0 
                records.append({
                    "employee_id": r.employee_id,
                    "date": r.date,
                    "check_in": r.check_in or '-',
                    "check_out": r.check_out or '-',
                    "hours": hours_worked_for_entry
                })

            total_hours_dict = attendance_manager.get_total_hours_for_employees(relevant_usernames)
            total_hours = sum(total_hours_dict.values()) if total_hours_dict else 0
        else:
            records = attendance_manager.get_attendance_for_employee(username)
            for r in records:
                hours_worked_for_entry = 0
                if r.get("check_in") and r.get("check_out"):
                    try:
                        in_time = datetime.strptime(r["check_in"], "%H:%M:%S")
                        out_time = datetime.strptime(r["check_out"], "%H:%M:%S")
                        delta = out_time - in_time
                        hours_worked_for_entry = round(delta.total_seconds() / 3600, 2)
                    except ValueError:
                        hours_worked_for_entry = 0
                r["hours"] = hours_worked_for_entry
            total_hours = attendance_manager.get_total_hours_for_employee(username)

    else: # Employee role
        records = attendance_manager.get_attendance_for_employee(username)
        for r in records:
            hours_worked_for_entry = 0
            if r.get("check_in") and r.get("check_out"):
                try:
                    in_time = datetime.strptime(r["check_in"], "%H:%M:%S")
                    out_time = datetime.strptime(r["check_out"], "%H:%M:%S")
                    delta = out_time - in_time
                    hours_worked_for_entry = round(delta.total_seconds() / 3600, 2)
                except ValueError:
                    hours_worked_for_entry = 0
            r["hours"] = hours_worked_for_entry
        total_hours = attendance_manager.get_total_hours_for_employee(username)

    return templates.TemplateResponse("attendance.html", {
        "request": request,
        "username": username,
        "role": role,
        "records": records,
        "total_hours": total_hours,
        "message": msg
    })

# ----------------------
# Notifications Route
# ----------------------
@app.get("/notifications", response_class=HTMLResponse)
async def notifications_page(request: Request):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")

    username = auth_manager.get_logged_in_user(token)
    role = auth_manager.get_user_role(token)

    # Get notifications for this user
    notifications = [
        n for n in inapp_notifier.notifications if n["to"] == username
    ][::-1]  # latest first

    return templates.TemplateResponse("notification.html", {
        "request": request,
        "username": username,
        "role": role,
        "notifications": notifications
    })


# ----------------------
# Payroll Module Integration
# ----------------------
@app.get("/payroll", response_class=HTMLResponse)
async def payroll_page(request: Request):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")
    
    username = auth_manager.get_logged_in_user(token)
    role = auth_manager.get_user_role(token)
    
    # Fetch all users for the payslip generation dropdown (for admins/managers)
    all_users = auth_manager.get_all_users()

    if role == "admin": # Admin sees all payslips
        slips = payroll_manager.get_all_payslips()
    elif role == "manager": # Manager sees payslips for their department and sub-departments
        manager_user_obj = next((u for u in auth_manager.get_all_users() if u['username'] == username), None)
        manager_dept_id = manager_user_obj['department_id'] if manager_user_obj else None

        if manager_dept_id:
            relevant_dept_ids = department_manager.get_all_department_ids_in_hierarchy(manager_dept_id)
            # Get usernames in these departments
            users_in_relevant_depts = auth_manager.get_users_by_department_ids(relevant_dept_ids)
            relevant_usernames = [u["username"] for u in users_in_relevant_depts]
            
            slips = payroll_manager.get_payslips_by_employees(relevant_usernames) # New method needed in payroll.py
        else:
            slips = [] # Manager not assigned to a department sees no payslips by default
    else: # Employee sees only their own payslips
        slips = payroll_manager.get_payslips_by_employee(username)

    # Pass the correct template and context
    return templates.TemplateResponse("payroll.html", { # <-- Corrected template name
        "request": request,
        "username": username,
        "role": role,
        "slips": slips, # <-- Ensure slips are passed
        "message": None, # Initial message is None
        "all_users": all_users # <-- Pass all_users for the dropdown
    })


@app.post("/payroll/generate")
async def generate_payslip(request: Request,
                           employee_id: str = Form(...),
                           base_salary: float = Form(...),
                           hours_worked: float = Form(...),
                           overtime_hours: float = Form(...),
                           month: str = Form(...),
                           year: int = Form(...)):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")

    username = auth_manager.get_logged_in_user(token)
    role = auth_manager.get_user_role(token)

    # Initialize message and slip (will be set to None if generation fails)
    message = None
    slip = None

    # Restrict payslip generation to only Admins
    if role != "admin":
        message = "Error: Only Admins can generate payslips."
        logger.log_event(username, "Payslip Generation Failed", {"reason": "Unauthorized role"})
    else:
        # Call generate_payslip and handle its new return format
        success, result = payroll_manager.generate_payslip(
            employee_id=employee_id,
            base_salary=base_salary,
            hours_worked=hours_worked,
            overtime_hours=overtime_hours,
            month=month,
            year=year
        )

        if success:
            slip = result # result is the payslip data dictionary
            message = f"Payslip generated! Net salary: BDT {slip['salary']}"
            logger.log_event(username, "Payslip Generated", {"employee_id": employee_id, "salary": slip['salary']})
        else:
            message = f"Error generating payslip: {result}" # result is the error message
            logger.log_event(username, "Payslip Generation Failed", {"employee_id": employee_id, "error": result})

    # Re-fetch slips based on role for the template response (consistent with GET /payroll)
    slips = [] 
    if role == "admin":
        slips = payroll_manager.get_all_payslips()
    elif role == "manager":
        manager_user_obj = next((u for u in auth_manager.get_all_users() if u['username'] == username), None)
        manager_dept_id = manager_user_obj['department_id'] if manager_user_obj else None
        if manager_dept_id:
            relevant_dept_ids = department_manager.get_all_department_ids_in_hierarchy(manager_dept_id)
            users_in_relevant_depts = auth_manager.get_users_by_department_ids(relevant_dept_ids)
            relevant_usernames = [u["username"] for u in users_in_relevant_depts]
            slips = payroll_manager.get_payslips_by_employees(relevant_usernames)
        else:
            slips = []
    else: # Employee
        slips = payroll_manager.get_payslips_by_employee(username)

    # Fetch all users for the dropdown (for admins/managers)
    all_users = auth_manager.get_all_users()

    return templates.TemplateResponse("payroll.html", {
        "request": request,
        "username": username,
        "role": role,
        "slips": slips,
        "message": message,
        "all_users": all_users
    })

@app.get("/payroll/download/{payslip_id}")
async def download_payslip(request: Request, payslip_id: int):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")
    
    username = auth_manager.get_logged_in_user(token)
    role = auth_manager.get_user_role(token) # <-- Add this line
    
    payslip_data = payroll_manager.get_payslip_by_id(payslip_id)
    
    # Basic authorization check: ensure the user can only download their own payslip
    # or if the user is an admin/manager (add role check if needed)
    # Allow download if it's the employee's own payslip OR if the user is an admin
    if not payslip_data or (payslip_data['employee_id'] != username and role != 'admin'):
        # For security, redirect to payroll page without revealing if payslip exists
        return RedirectResponse(url="/payroll", status_code=303)
    
    # Generate the PDF into an in-memory BytesIO object
    pdf_bytes_io = pdf_payslip_generator.generate_payslip_pdf(payslip_data)
    
    # Set the BytesIO object's cursor to the beginning
    pdf_bytes_io.seek(0)
    
    # Return the FileResponse with the BytesIO object
    return StreamingResponse(
        pdf_bytes_io, # Pass the BytesIO object directly
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="payslip_{payslip_id}.pdf"'}
    )



from report_manager import ReportManager

report_manager = ReportManager()

# ----------------------
# Reports Route
# ----------------------
@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")

    username = auth_manager.get_logged_in_user(token)
    role = auth_manager.get_user_role(token)

    task_report = {}
    total_hours = {}
    total_pay = {}

    if role == 'admin': # Admin sees all reports
        task_report = report_manager.get_task_report_by_employee()
        total_hours = report_manager.get_total_hours_by_employee()
        total_pay = report_manager.get_total_pay_by_employee()
    elif role == 'manager': # Manager sees reports for their department and sub-departments
        manager_user_obj = next((u for u in auth_manager.get_all_users() if u['username'] == username), None)
        manager_dept_id = manager_user_obj['department_id'] if manager_user_obj else None

        if manager_dept_id:
            relevant_dept_ids = department_manager.get_all_department_ids_in_hierarchy(manager_dept_id)
            task_report = report_manager.get_task_report_by_department_ids(relevant_dept_ids)
            total_hours = report_manager.get_total_hours_by_department_ids(relevant_dept_ids)
            total_pay = report_manager.get_total_pay_by_department_ids(relevant_dept_ids)
        # If manager has no department, reports will be empty as initialized
    # Employees don't access this page (handled by main.py route guard)
    return templates.TemplateResponse("reports.html", {
        "request": request,
        "username": username,
        "role": role,
        "task_report": task_report,
        "total_hours": total_hours,
        "total_pay": total_pay
    })

@app.get("/reports/download/tasks")
async def download_task_report(request: Request):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")

    role = auth_manager.get_user_role(token)
    if role not in ["admin", "manager"]:
        return RedirectResponse(url="/dashboard")

    filename = pdf_generator.generate_task_report_pdf()

    return FileResponse(
        filename,
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )



from task_manager import TaskManager

task_manager = TaskManager(notifier=inapp_notifier)

# ----------------------
# Task Manager Routes
# ----------------------
@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")

    username = auth_manager.get_logged_in_user(token)
    role = auth_manager.get_user_role(token)
    # Initialize tasks list
    tasks = []

    if role == 'admin': # Admin sees ALL tasks
        tasks = task_manager.get_all_tasks()
        
    elif role == 'manager': # Manager sees tasks for their department and sub-departments
        # Get the manager's department ID
        manager_user_obj = next((u for u in auth_manager.get_all_users() if u['username'] == username), None)
        manager_dept_id = manager_user_obj['department_id'] if manager_user_obj else None

        if manager_dept_id:
            # Get all relevant department IDs (manager's dept + its children)
            relevant_dept_ids = department_manager.get_all_department_ids_in_hierarchy(manager_dept_id)
            
            # Fetch users in these departments
            users_in_relevant_depts = auth_manager.get_users_by_department_ids(relevant_dept_ids)
            relevant_usernames = [u["username"] for u in users_in_relevant_depts]

            # Fetch tasks for these users
            tasks = task_manager.get_tasks_for_employees(relevant_usernames) # New method
        else:
            # Manager not assigned to a department, show only their own tasks
            tasks = task_manager.get_tasks_by_user(username)
            
    else: # Employee role
        tasks = task_manager.get_tasks_by_user(username)
    
    # Fetch all users initially
    all_users_for_dropdown = auth_manager.get_all_users()

    # Initialize tasks list
    tasks = []

    if role == 'admin': # Admin sees ALL tasks and can assign to anyone
        tasks = task_manager.get_all_tasks()
        all_users = all_users_for_dropdown # Admin can assign to all users
        
    elif role == 'manager': # Manager sees tasks for their department and sub-departments, and can assign to users in those depts
        manager_user_obj = next((u for u in all_users_for_dropdown if u['username'] == username), None)
        manager_dept_id = manager_user_obj['department_id'] if manager_user_obj else None

        if manager_dept_id:
            relevant_dept_ids = department_manager.get_all_department_ids_in_hierarchy(manager_dept_id)
            users_in_relevant_depts = auth_manager.get_users_by_department_ids(relevant_dept_ids)
            relevant_usernames = [u["username"] for u in users_in_relevant_depts]
            tasks = task_manager.get_tasks_for_employees(relevant_usernames)
            all_users = users_in_relevant_depts # Manager can only assign to users in relevant depts
        else:
            # Manager not assigned to a department, show only their own tasks and can only assign to themselves
            tasks = task_manager.get_tasks_by_user(username)
            all_users = [{'username': username, 'role': role, 'department_id': manager_dept_id}] # Can only assign to self
            
    else: # Employee role - sees only their own tasks and can only assign to themselves
        tasks = task_manager.get_tasks_by_user(username)
        all_users = [{'username': username, 'role': role, 'department_id': None}] # Can only assign to self

    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "username": username,
        "role": role,
        "tasks": tasks,
        "message": None,
        "all_users": all_users  # Pass the list of all users
    })

@app.post("/tasks/create")
async def create_task(request: Request,
                      title: str = Form(...),
                      description: str = Form(...),
                      assigned_to: str = Form(...),
                      deadline: str = Form(...),
                      task_type: str = Form("Task")):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")

    username = auth_manager.get_logged_in_user(token)
    role = auth_manager.get_user_role(token)
    message = None # Initialize message

    try:
        task_manager.create_task(title, description, assigned_to, deadline, task_type)
        message = "Task created successfully!"
        logger.log_event(username, "Task Created", {"title": title, "assigned_to": assigned_to})
    except Exception as e:
        message = f"Error creating task: {str(e)}"
        logger.log_event(username, "Task Creation Failed", {"title": title, "error": str(e)})

    # Reload tasks and all users based on role
    tasks = [] # Initialize tasks list
    if role == 'admin': # Admin sees ALL tasks
        tasks = task_manager.get_all_tasks()
        
    elif role == 'manager': # Manager sees tasks for their department and sub-departments
        manager_user_obj = next((u for u in auth_manager.get_all_users() if u['username'] == username), None)
        manager_dept_id = manager_user_obj['department_id'] if manager_user_obj else None

        if manager_dept_id:
            relevant_dept_ids = department_manager.get_all_department_ids_in_hierarchy(manager_dept_id)
            users_in_relevant_depts = auth_manager.get_users_by_department_ids(relevant_dept_ids)
            relevant_usernames = [u["username"] for u in users_in_relevant_depts]
            tasks = task_manager.get_tasks_for_employees(relevant_usernames)
        else:
            tasks = task_manager.get_tasks_by_user(username)
            
    else: # Employee role
        tasks = task_manager.get_tasks_by_user(username)
    
    # Re-evaluate all_users for dropdown based on role after task creation
    all_users_for_dropdown = auth_manager.get_all_users() # Fetch all users initially for manager logic

    if role == 'admin':
        all_users = all_users_for_dropdown
    elif role == 'manager':
        manager_user_obj = next((u for u in all_users_for_dropdown if u['username'] == username), None)
        manager_dept_id = manager_user_obj['department_id'] if manager_user_obj else None
        if manager_dept_id:
            relevant_dept_ids = department_manager.get_all_department_ids_in_hierarchy(manager_dept_id)
            all_users = auth_manager.get_users_by_department_ids(relevant_dept_ids)
        else:
            all_users = [{'username': username, 'role': role, 'department_id': manager_dept_id}]
    else:
        all_users = [{'username': username, 'role': role, 'department_id': None}] # Employee can only assign to self # Always fetch all users for the dropdown

    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "username": username,
        "role": role,
        "tasks": tasks,
        "message": message,
        "all_users": all_users
    })

@app.post("/tasks/update_status")
async def update_task_status(request: Request, task_id: str = Form(...), new_status: str = Form(...)):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")

    username = auth_manager.get_logged_in_user(token)
    role = auth_manager.get_user_role(token)
    
    # Check if the user is authorized to update this task
    task = task_manager.get_task_by_id(task_id)
    if task and task.get('assigned_to') != username and role != 'admin':
        return RedirectResponse(url="/dashboard?message=Unauthorized to update this task.")

    success, msg = task_manager.update_task_status(task_id, new_status)
    
    # Log the event
    logger.log_event(username, "Task Status Updated", {"task_id": task_id, "new_status": new_status})
    
    # Reload tasks and return to the page
    tasks = task_manager.get_tasks_by_user(username)
    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "username": username,
        "role": role,
        "tasks": tasks,
        "message": msg
    })

# ----------------------
# Admin Routes
# ----------------------
@app.get("/admin/users", response_class=HTMLResponse)
async def user_management_page(request: Request, message: str | None = None):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")

    username = auth_manager.get_logged_in_user(token)
    role = auth_manager.get_user_role(token)

    if role != "admin":
        return RedirectResponse(url="/dashboard")
    
    all_users = auth_manager.get_all_users()
    departments = department_manager.get_all_departments_db() # Fetch all departments

    return templates.TemplateResponse("user_management.html", {
        "request": request,
        "username": username,
        "role": role,
        "all_users": all_users,
        "departments": departments, # <-- Ensure this line is present
        "message": message
    })

@app.post("/admin/update_role")
async def update_user_role(request: Request, username: str = Form(...), new_role: str = Form(...), department_id: Optional[int] = Form(None)):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")

    admin_username = auth_manager.get_logged_in_user(token)
    current_role = auth_manager.get_user_role(token)
    if current_role != "admin":
        return RedirectResponse(url="/dashboard")

    success, msg = auth_manager.update_user_role(admin_username, username, new_role, department_id if department_id != 0 else None)
    
    # Redirect back to the user management page with the message as a query parameter
    return RedirectResponse(f"/admin/users?message={msg}", status_code=303)

# ----------------------
# Audit Logs Route
# ----------------------
@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")

    username = auth_manager.get_logged_in_user(token)
    role = auth_manager.get_user_role(token)
    if role != "admin":
        return RedirectResponse(url="/dashboard")

    logs = logger.get_logs()[::-1]  # Latest first

    return templates.TemplateResponse("logs.html", {
        "request": request,
        "username": username,
        "role": role,
        "logs": logs
    })

# ----------------------
# Department Management Routes
# ----------------------
@app.get("/admin/departments", response_class=HTMLResponse)
async def department_management_page(request: Request, message: str | None = None):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")

    username = auth_manager.get_logged_in_user(token)
    role = auth_manager.get_user_role(token)

    if role != "admin":
        return RedirectResponse(url="/dashboard?message=Unauthorized access to department management.")

    departments_flat = department_manager.get_all_departments_db() # Get flat list for dropdowns
    department_tree = department_manager.get_department_tree() # Get hierarchical structure for display

    return templates.TemplateResponse("department_management.html", {
        "request": request,
        "username": username,
        "role": role,
        "departments": departments_flat, # Pass flat list for forms
        "department_tree": department_tree, # Pass tree for display
        "message": message
    })

@app.post("/admin/departments/create")
async def create_department(request: Request, name: str = Form(...), parent_id: Optional[int] = Form(None)):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")

    role = auth_manager.get_user_role(token)
    if role != "admin":
        return RedirectResponse(url="/dashboard?message=Unauthorized to create departments.")

    # Use the direct DB method from DepartmentManager
    success, msg = department_manager.create_department_db(name, parent_id if parent_id != 0 else None)
    
    return RedirectResponse(f"/admin/departments?message={msg}", status_code=303)

@app.post("/admin/departments/update")
async def update_department(request: Request, dept_id: int = Form(...), new_name: str = Form(...), new_parent_id: Optional[int] = Form(None)):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")

    role = auth_manager.get_user_role(token)
    if role != "admin":
        return RedirectResponse(url="/dashboard?message=Unauthorized to update departments.")

    success, msg = department_manager.update_department_db(dept_id, new_name, new_parent_id if new_parent_id != 0 else None)
    
    return RedirectResponse(f"/admin/departments?message={msg}", status_code=303)

@app.post("/admin/departments/delete")
async def delete_department(request: Request, dept_id: int = Form(...)):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")

    role = auth_manager.get_user_role(token)
    if role != "admin":
        return RedirectResponse(url="/dashboard?message=Unauthorized to delete departments.")

    success, msg = department_manager.delete_department_db(dept_id)
    
    return RedirectResponse(f"/admin/departments?message={msg}", status_code=303)