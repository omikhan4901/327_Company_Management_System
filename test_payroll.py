# test_payroll.py

import os
import pytest
import time # Added for time.sleep
from payroll import PayrollManager, ConcreteStrategyA, ConcreteStrategyB
from notification import NotificationManager, InAppNotifier # For notifier integration
from database import create_tables, SessionLocal, Payslip, engine # Import engine

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

def test_payslip_generation_strategy_a():
    print("\n--- Payslip Generation (Standard Hourly) Test ---")
    notifier = NotificationManager()
    in_app_notifier = InAppNotifier(notifier.subject) # To capture notifications
    pm = PayrollManager(strategy=ConcreteStrategyA(), notifier=notifier)

    employee_id = "employee_hourly"
    base_salary = 50000
    hours_worked = 160
    overtime_hours = 10
    month = "August"
    year = 2025

    success, payslip_data = pm.generate_payslip(
        employee_id=employee_id,
        base_salary=base_salary,
        hours_worked=hours_worked,
        overtime_hours=overtime_hours,
        month=month,
        year=year
    )
    assert success is True
    assert payslip_data is not None
    assert payslip_data['employee_id'] == employee_id
    assert payslip_data['strategy'] == "Standard Hourly Pay"
    
    # Expected salary: (160 + 10*1.5) * (50000/160) = (160 + 15) * 312.5 = 175 * 312.5 = 54687.5
    assert payslip_data['salary'] == 54687.5
    print(f"Generated Payslip (Standard): {payslip_data['salary']} for {employee_id}")

    # Verify notification sent
    assert any(f"Payslip for {month} {year} generated. Net salary: BDT {payslip_data['salary']}" in n['message'] for n in in_app_notifier.notifications if n['to'] == employee_id)
    print("Notification verified for payslip generation.")

def test_payslip_generation_strategy_b():
    print("\n--- Payslip Generation (Sales Commission) Test ---")
    pm = PayrollManager(strategy=ConcreteStrategyB(commission_rate=0.05))

    employee_id = "employee_sales"
    base_salary = 30000
    sales_amount = 100000
    month = "September"
    year = 2025

    success, payslip_data = pm.generate_payslip(
        employee_id=employee_id,
        base_salary=base_salary,
        hours_worked=160, # Not used in this strategy, but required by method signature
        overtime_hours=0, # Not used in this strategy, but required by method signature
        month=month,
        year=year,
        sales=sales_amount
    )
    assert success is True
    assert payslip_data is not None
    assert payslip_data['employee_id'] == employee_id
    assert payslip_data['strategy'] == "Sales Commission Pay"
    
    # Expected salary: 30000 + (100000 * 0.05) = 30000 + 5000 = 35000
    assert payslip_data['salary'] == 35000.0
    print(f"Generated Payslip (Sales): {payslip_data['salary']} for {employee_id}")

def test_payslip_retrieval():
    print("\n--- Payslip Retrieval Test ---")
    pm = PayrollManager()

    # Generate a few payslips
    pm.generate_payslip("user1", 40000, 160, 0, "Jan", 2025)
    pm.generate_payslip("user2", 60000, 160, 5, "Jan", 2025)
    pm.generate_payslip("user1", 42000, 160, 0, "Feb", 2025)

    # Get payslips by single employee
    user1_slips = pm.get_payslips_by_employee("user1")
    assert len(user1_slips) == 2
    print(f"Payslips for user1: {[s['month'] for s in user1_slips]}")

    # Get all payslips
    all_slips = pm.get_all_payslips()
    assert len(all_slips) == 3
    print(f"All payslips: {len(all_slips)} total.")

    # Get payslip by ID
    first_slip_id = all_slips[0]['slip_id']
    retrieved_slip = pm.get_payslip_by_id(first_slip_id)
    assert retrieved_slip is not None
    assert retrieved_slip['slip_id'] == first_slip_id
    print(f"Retrieved payslip by ID: {retrieved_slip['employee_id']} - {retrieved_slip['month']}")

    # Get payslips by multiple employees (for manager view)
    selected_employee_slips = pm.get_payslips_by_employees(["user1", "user2"])
    assert len(selected_employee_slips) == 3
    print(f"Payslips for selected employees: {len(selected_employee_slips)} total.")
