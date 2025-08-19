from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from authentication import AuthManager
from attendance import AttendanceManager, format_records
from notification import NotificationManager, InAppNotifier
from payroll import PayrollManager, ConcreteStrategyA

app = FastAPI()
auth_manager = AuthManager.get_instance()
attendance_manager = AttendanceManager()
notification_manager = NotificationManager()
inapp_notifier = InAppNotifier(notification_manager.subject)

# Pass NotificationManager to PayrollManager, not InAppNotifier
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
        return templates.TemplateResponse("login.html", {"request": request, "error": result, "username": None})
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="session_token", value=result, httponly=True)
    return response


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "username": None})


@app.post("/register")
async def register_user(request: Request,
                        username: str = Form(...),
                        password: str = Form(...),
                        role: str = Form(...)):
    success, msg = auth_manager.register_user(username, password, role)
    if not success:
        return templates.TemplateResponse("register.html", {"request": request, "error": msg, "username": None})
    success, token = auth_manager.login(username, password)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="session_token", value=token, httponly=True)
    return response


@app.get("/logout")
async def logout(request: Request):
    token = request.cookies.get("session_token")
    if token:
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
    records = attendance_manager.get_attendance_for_employee(username)
    records = format_records(records)
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
    success, msg = attendance_manager.check_in(username)
    notification_manager.send_notification(msg, username)

    records = attendance_manager.get_attendance_for_employee(username)
    records = format_records(records)
    total_hours = attendance_manager.get_total_hours_for_employee(username)

    return templates.TemplateResponse("attendance.html", {
        "request": request,
        "username": username,
        "role": auth_manager.get_user_role(token),
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
    success, msg = attendance_manager.check_out(username)
    notification_manager.send_notification(msg, username)

    records = attendance_manager.get_attendance_for_employee(username)
    records = format_records(records)
    total_hours = attendance_manager.get_total_hours_for_employee(username)

    return templates.TemplateResponse("attendance.html", {
        "request": request,
        "username": username,
        "role": auth_manager.get_user_role(token),
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

    slips = payroll_manager.get_payslips_by_employee(username)

    return templates.TemplateResponse("payroll.html", {
        "request": request,
        "username": username,
        "role": role,
        "slips": slips,
        "message": None
    })


@app.post("/payroll/generate")
async def generate_payslip(request: Request, base_salary: float = Form(...), hours_worked: float = Form(...),
                           overtime_hours: float = Form(...), month: str = Form(...), year: int = Form(...)):
    token = request.cookies.get("session_token")
    if not token or not auth_manager.validate_token(token):
        return RedirectResponse(url="/login")
    
    username = auth_manager.get_logged_in_user(token)
    role = auth_manager.get_user_role(token)

    slip = payroll_manager.generate_payslip(
        employee_id=username,
        base_salary=base_salary,
        hours_worked=hours_worked,
        overtime_hours=overtime_hours,
        month=month,
        year=year
    )

    slips = payroll_manager.get_payslips_by_employee(username)
    message = f"Payslip generated! Net salary: BDT {slip['salary']}"

    return templates.TemplateResponse("payroll.html", {
        "request": request,
        "username": username,
        "role": role,
        "slips": slips,
        "message": message
    })

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

    task_report = report_manager.get_task_report_by_employee()
    total_hours = report_manager.get_total_hours_by_employee()
    total_pay = report_manager.get_total_pay_by_employee()

    return templates.TemplateResponse("reports.html", {
        "request": request,
        "username": username,
        "role": role,
        "task_report": task_report,
        "total_hours": total_hours,
        "total_pay": total_pay
    })

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
    tasks = task_manager.get_tasks_by_user(username)

    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "username": username,
        "role": role,
        "tasks": tasks,
        "message": None
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

    try:
        task_manager.create_task(title, description, assigned_to, deadline, task_type)
        message = "Task created successfully!"
    except Exception as e:
        message = f"Error creating task: {str(e)}"

    # Reload tasks after creation
    tasks = task_manager.get_tasks_by_user(username)

    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "username": username,
        "role": role,
        "tasks": tasks,
        "message": message
    })
