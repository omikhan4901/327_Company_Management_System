# test_reports.py

import os
import pytest
import time # Added for time.sleep
from datetime import datetime, timedelta
from report_facade import ReportFacade
from report_manager import ReportManager
from task_manager import TaskManager, TaskStatus
from attendance import AttendanceManager
from payroll import PayrollManager, ConcreteStrategyA
from authentication import AuthManager
from database import create_tables, SessionLocal, User, Department, Task, Attendance, Payslip, engine # Import engine
from department_manager import DepartmentManager # Import DepartmentManager here
import hashlib # For password hashing in user setup

# Helper function to clean up database and set up initial data
@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    # Helper to force-delete the database file, with retries
    def force_delete_db():
        SessionLocal.remove() # Ensure session is removed
        engine.dispose() # Dispose of the engine to release file lock
        if os.path.exists("company.db"):
            for i in range(5):
                try:
                    os.remove("company.db")
                    break # Success!
                except PermissionError as e:
                    print(f"Failed to delete DB, retrying... ({i+1}/5)")
                    time.sleep(0.1) # Wait for 1 second before retrying
                    if i == 4:
                        raise e # Re-raise if all retries fail
    
    # --- Setup Phase ---
    force_delete_db() # Call the helper before setup
    create_tables()

    # Initialize managers (ensure singletons are reset or correctly fetched)
    auth_manager = AuthManager.get_instance()
    dept_manager = DepartmentManager()
    
    # Create default admin and department
    auth_manager.create_default_admin()
    dept_manager.create_default_department()

    # Use a single session for all setup data creation
    db = SessionLocal()
    try:
        # Create departments and get their IDs immediately
        hr_dept_obj = Department(name="HR", parent_department_id=None)
        dev_dept_obj = Department(name="Development", parent_department_id=None)
        db.add_all([hr_dept_obj, dev_dept_obj])
        db.commit() # Commit to get IDs
        db.refresh(hr_dept_obj) # Refresh to ensure IDs are loaded into objects
        db.refresh(dev_dept_obj)

        qa_dept_obj = Department(name="QA", parent_department_id=dev_dept_obj.id) # Use dev_dept_obj.id
        db.add(qa_dept_obj)
        db.commit() # Commit to get ID
        db.refresh(qa_dept_obj)

        # Capture IDs after refresh and before session close
        hr_dept_id = hr_dept_obj.id
        dev_dept_id = dev_dept_obj.id
        qa_dept_id = qa_dept_obj.id

        # Create users and assign to departments using IDs
        user_admin = db.query(User).filter(User.username == "admin").first()
        user_admin.department_id = hr_dept_id # Assign admin to HR
        
        user_manager_dev = User(username="dev_mgr", password_hash=hashlib.sha256("hash".encode()).hexdigest(), role="manager", department_id=dev_dept_id)
        user_employee_dev = User(username="dev_emp", password_hash=hashlib.sha256("hash".encode()).hexdigest(), role="employee", department_id=dev_dept_id)
        user_employee_qa = User(username="qa_emp", password_hash=hashlib.sha256("hash".encode()).hexdigest(), role="employee", department_id=qa_dept_id)
        user_employee_unassigned = User(username="unassigned_emp", password_hash=hashlib.sha256("hash".encode()).hexdigest(), role="employee", department_id=None) # Unassigned
        db.add_all([user_manager_dev, user_employee_dev, user_employee_qa, user_employee_unassigned])
        db.commit() # Commit user creations and updates

        # Initialize managers needed for data creation (they will use their own sessions internally)
        task_mgr = TaskManager()
        att_mgr = AttendanceManager()
        payroll_mgr = PayrollManager()

        # Create tasks
        task_mgr.create_task("Dev Task 1", "Desc", "dev_emp", "2025-09-01")
        task_mgr.create_task("QA Task 1", "Desc", "qa_emp", "2025-09-05")
        task_mgr.create_task("Dev Task 2", "Desc", "dev_emp", "2025-09-10", task_type="HighPriorityTask")
        task_mgr.create_task("Admin Task", "Desc", "admin", "2025-09-15")
        
        # Ensure one task is in progress for assertion
        # Fetch task by ID to ensure it's "live" in its own session if task_mgr uses one
        qa_task_data = task_mgr.get_tasks_by_user("qa_emp")[0] # This returns dict, so ID is fine
        task_mgr.update_task_status(qa_task_data['id'], TaskStatus.IN_PROGRESS.value) # Set to In Progress

        # Complete one dev_emp task
        dev_emp_task_data = task_mgr.get_tasks_by_user("dev_emp")[0]
        task_mgr.update_task_status(dev_emp_task_data['id'], TaskStatus.COMPLETED.value) 

        # Create attendance records using direct db.add for explicit department_id
        # Ensure these are committed within the same session or via manager methods
        db.add(Attendance(employee_id="dev_emp", date=datetime.now().strftime("%Y-%m-%d"), 
                          check_in="09:00:00", check_out="17:00:00", department_id=dev_dept_id)) # 8 hours today
        db.add(Attendance(employee_id="dev_emp", date=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"), 
                          check_in="08:00:00", check_out="16:00:00", department_id=dev_dept_id)) # 8 hours yesterday
        db.add(Attendance(employee_id="qa_emp", date=datetime.now().strftime("%Y-%m-%d"), 
                          check_in="09:00:00", check_out="17:00:00", department_id=qa_dept_id)) # 8 hours today
        db.commit() # Commit all manual attendance additions in this session

        # Create payslips
        payroll_mgr.generate_payslip("dev_emp", 50000, 160, 5, "August", 2025)
        payroll_mgr.generate_payslip("qa_emp", 45000, 160, 0, "August", 2025)
        payroll_mgr.generate_payslip("admin", 70000, 160, 0, "August", 2025)

    finally:
        db.close() # Close the session used for setup data
    
    yield # Run the actual test function
    
    # --- Teardown Phase ---
    force_delete_db() # Call the helper after the test

def test_report_facade_employee_summary():
    print("\n--- Report Facade: Employee Summary Test ---")
    facade = ReportFacade()
    
    dev_emp_summary = facade.get_employee_summary("dev_emp")
    assert len(dev_emp_summary['tasks']) == 2
    assert any(t['status'] == TaskStatus.COMPLETED.value for t in dev_emp_summary['tasks'])
    assert len(dev_emp_summary['payslips']) == 1
    assert dev_emp_summary['total_hours'] == 16.0 # Corrected expected value: 8 + 8 = 16
    assert dev_emp_summary['total_pay'] > 0
    print(f"Dev Employee Summary: {dev_emp_summary}")

    qa_emp_summary = facade.get_employee_summary("qa_emp")
    assert len(qa_emp_summary['tasks']) == 1
    assert len(qa_emp_summary['payslips']) == 1
    assert qa_emp_summary['total_hours'] == 8.0
    assert qa_emp_summary['total_pay'] > 0
    print(f"QA Employee Summary: {qa_emp_summary}")

 
def test_report_manager_department_filtered_reports():
    print("\n--- Report Manager: Department Filtered Reports Test ---")
    report_manager = ReportManager()
    dept_manager = DepartmentManager()

    # Get Development department hierarchy IDs (Development + QA)
    # Re-query departments to ensure they are "live" in this context
    db = SessionLocal()
    try:
        dev_dept = db.query(Department).filter(Department.name == "Development").first()
        qa_dept = db.query(Department).filter(Department.name == "QA").first()
    finally:
        db.close()

    assert dev_dept is not None
    assert qa_dept is not None

    dev_hierarchy_ids = dept_manager.get_all_department_ids_in_hierarchy(dev_dept.id)
    print(f"Development hierarchy IDs: {dev_hierarchy_ids}")
    assert dev_dept.id in dev_hierarchy_ids
    assert qa_dept.id in dev_hierarchy_ids
    assert len(dev_hierarchy_ids) == 2 # Development and QA

    # Test task report by department IDs
    dept_tasks = report_manager.get_task_report_by_department_ids(dev_hierarchy_ids)
    assert len(dept_tasks) == 2 # dev_emp, qa_emp
    assert "dev_emp" in dept_tasks
    assert "qa_emp" in dept_tasks
    assert len(dept_tasks["dev_emp"]) == 2
    assert len(dept_tasks["qa_emp"]) == 1
    print(f"Tasks for Dev/QA departments: {dept_tasks}")

    # Test total hours by department IDs
    dept_hours = report_manager.get_total_hours_by_department_ids(dev_hierarchy_ids)
    assert dept_hours["dev_emp"] == 16.0 # Corrected expected value
    assert dept_hours["qa_emp"] == 8.0 # Corrected expected value
    print(f"Total hours for Dev/QA departments: {dept_hours}")

    # Test total pay by department IDs
    dept_pay = report_manager.get_total_pay_by_department_ids(dev_hierarchy_ids)
    assert dept_pay["dev_emp"] > 0
    assert dept_pay["qa_emp"] > 0
    print(f"Total pay for Dev/QA departments: {dept_pay}")
