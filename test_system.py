# test/test_system.py

from notification import NotificationManager, InAppNotifier, EmailNotifier
from payroll import PayrollManager
from task_manager import TaskManager
from attendance import AttendanceManager
from report_facade import ReportFacade

# 1. Setup notification system
notify = NotificationManager()
in_app = InAppNotifier()
email = EmailNotifier()

notify.add_notifier(in_app)
notify.add_notifier(email)

# 2. Setup all managers using the shared notifier
task_mgr = TaskManager(notifier=notify)
payroll_mgr = PayrollManager(notifier=notify)
attendance_mgr = AttendanceManager(notifier=notify)

# 3. Simulate Attendance
print("\n--- [Attendance] Check-in ---")
success, msg = attendance_mgr.check_in("john")
print(msg)

print("\n--- [Attendance] Check-out ---")
success, msg = attendance_mgr.check_out("john")
print(msg)

# 4. Simulate Task Assignment
print("\n--- [Task] Create Task ---")
task_id = task_mgr.create_task(
    title="Write unit tests",
    description="Create pytest test suite for Payroll",
    assigned_to="john",
    deadline="2025-08-10"
)
print(f"Created Task ID: {task_id}")

# 5. Simulate Payslip Generation
print("\n--- [Payroll] Generate Payslip ---")
slip = payroll_mgr.generate_payslip(
    employee_id="john",
    base_salary=30000,
    hours_worked=160,
    overtime_hours=5,
    month="August",
    year=2025
)
print(slip)

# 6. View all notifications stored in-app
print("\n--- [Notifications] In-App Notification Log ---")
for note in in_app.notifications:
    print(note)

# 7. Generate Reports using ReportFacade
print("\n--- [Reports] Employee Summary for john ---")
report_facade = ReportFacade()
summary = report_facade.get_employee_summary("john")

for key, val in summary.items():
    print(f"{key}:\n{val}")

print("\n--- [Reports] System Summary ---")
system_summary = report_facade.get_system_summary()
for key, val in system_summary.items():
    print(f"{key}:\n{val}")
