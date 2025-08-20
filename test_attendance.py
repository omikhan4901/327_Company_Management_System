# test_attendance.py

import os
import pytest
import time # Added for time.sleep
from datetime import datetime, timedelta
from attendance import AttendanceManager
from notification import NotificationManager, InAppNotifier # For notifier integration
from database import create_tables, SessionLocal, Attendance, engine # Import engine
from collections import defaultdict # Added for get_total_hours_for_employees in test

# Helper function to clean up database
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
    
    yield # Run the test here
    
    # --- Teardown Phase ---
    force_delete_db() # Call the helper after the test

def test_check_in_and_check_out():
    print("\n--- Check-in/Check-out Test ---")
    notifier = NotificationManager()
    in_app_notifier = InAppNotifier(notifier.subject) # To capture notifications
    am = AttendanceManager(notifier=notifier)

    employee_id = "test_employee_att"
    
    # Test successful check-in
    success, msg = am.check_in(employee_id)
    assert success is True
    assert "Check-in successful" in msg
    print(f"Check-in: {msg}")

    # Try to check-in again on the same day (should fail)
    success, msg = am.check_in(employee_id)
    assert success is False
    assert "Already checked in today." in msg
    print(f"Second Check-in (same day): {msg}")

    # Test check-out without prior check-in (should fail if no open entry)
    success, msg = am.check_out("another_employee")
    assert success is False
    assert "No check-in found for today." in msg
    print(f"Check-out (no prior check-in): {msg}")

    # Test successful check-out
    success, msg = am.check_out(employee_id)
    assert success is True
    assert "Check-out successful" in msg
    print(f"Check-out: {msg}")

    # Verify notification sent
    assert any("Checked in at" in n['message'] for n in in_app_notifier.notifications if n['to'] == employee_id)
    assert any("Checked out at" in n['message'] for n in in_app_notifier.notifications if n['to'] == employee_id)
    print("Notifications verified for check-in/out.")

def test_attendance_records_and_total_hours():
    print("\n--- Attendance Records and Total Hours Test ---")
    am = AttendanceManager()
    employee1 = "emp1" 
    employee2 = "emp2" 
    today_str = datetime.now().strftime("%Y-%m-%d")
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Manually add some attendance data for calculation within a session
    db = SessionLocal()
    try:
        # Emp1: 8 hours today + 8 hours yesterday = 16 hours
        db.add(Attendance(employee_id=employee1, date=today_str, check_in="09:00:00", check_out="17:00:00"))
        db.add(Attendance(employee_id=employee1, date=yesterday_str, check_in="08:00:00", check_out="16:00:00"))
        # Emp2: 7 hours today
        db.add(Attendance(employee_id=employee2, date=today_str, check_in="10:00:00", check_out="17:00:00"))
        db.commit()
    finally:
        db.close()

    # Test get_attendance_for_employee
    emp1_records = am.get_attendance_for_employee(employee1)
    assert len(emp1_records) == 2
    print(f"Records for {employee1}: {emp1_records}")

    # Test get_total_hours_for_employee
    emp1_total_hours = am.get_total_hours_for_employee(employee1)
    assert emp1_total_hours == 16.0 # Corrected expected value: 8 + 8 = 16
    print(f"Total hours for {employee1}: {emp1_total_hours}")

    # Test get_all_attendance_records (for admin view)
    all_records = am.get_all_attendance_records()
    assert len(all_records) == 3
    print(f"All records: {len(all_records)} entries.")

    # Test get_total_hours_for_all_employees (for admin view)
    all_employees_total_hours = am.get_total_hours_for_all_employees()
    assert all_employees_total_hours[employee1] == 16.0
    assert all_employees_total_hours[employee2] == 7.0
    print(f"Total hours for all employees: {all_employees_total_hours}")

    # Test get_attendance_for_employees (for manager view)
    selected_employees_records = am.get_attendance_for_employees([employee1])
    assert len(selected_employees_records) == 2
    print(f"Records for selected employees ({employee1}): {len(selected_employees_records)} entries.")

    # Test get_total_hours_for_employees (for manager view)
    selected_employees_total_hours = am.get_total_hours_for_employees([employee1, employee2])
    assert selected_employees_total_hours[employee1] == 16.0
    assert selected_employees_total_hours[employee2] == 7.0
    print(f"Total hours for selected employees ({employee1}, {employee2}): {selected_employees_total_hours}")
