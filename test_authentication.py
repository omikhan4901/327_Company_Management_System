# test_authentication.py

import os
import pytest
import time # Added for time.sleep
import hashlib # Added for password hashing
from authentication import AuthManager
from database import create_tables, SessionLocal, User, Department, engine # Import engine
from department_manager import DepartmentManager

# Helper function to clean up database and create default admin/department
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
                    time.sleep(0.1) # Shorten sleep slightly for faster retries
                    if i == 4:
                        raise e # Re-raise if all retries fail
    
    # --- Setup Phase ---
    force_delete_db() # Call the helper before setup
    create_tables()
    
    # Initialize managers and create default data for tests
    auth_manager = AuthManager.get_instance()
    auth_manager.create_default_admin()
    dept_manager = DepartmentManager()
    dept_manager.create_default_department()
    
    yield # Run the test here
    
    # --- Teardown Phase ---
    force_delete_db() # Call the helper after the test

def test_auth_manager_singleton():
    print("\n--- Singleton Test ---")
    auth1 = AuthManager.get_instance()
    auth2 = AuthManager.get_instance()
    assert auth1 is auth2
    print("Singleton test passed: AuthManager instances are the same.")

def test_user_registration_and_login():
    print("\n--- User Registration and Login Test ---")
    auth_manager = AuthManager.get_instance()

    # Test default employee registration
    success, msg = auth_manager.register_user("test_employee", "pass123", "employee")
    assert success is True
    assert "User registered successfully." in msg
    print(f"Registration (Employee): {msg}")

    # Test admin login
    success, token = auth_manager.login("admin", "admin")
    assert success is True
    assert token is not None
    print(f"Admin Login: {'Success' if success else msg}")

    # Test employee login
    success, token_employee = auth_manager.login("test_employee", "pass123")
    assert success is True
    assert token_employee is not None
    print(f"Employee Login: {'Success' if success else msg}")

    # Test invalid login
    success, msg = auth_manager.login("non_existent", "wrong_pass")
    assert success is False
    assert "User not found." in msg
    print(f"Invalid Login (Non-existent): {msg}")

    success, msg = auth_manager.login("test_employee", "wrong_pass")
    assert success is False
    assert "Invalid password." in msg
    print(f"Invalid Login (Wrong Pass): {msg}")

def test_user_role_and_department_update():
    print("\n--- User Role and Department Update Test ---")
    auth_manager = AuthManager.get_instance()
    dept_manager = DepartmentManager()

    # Create a test employee and a department
    auth_manager.register_user("john_doe", "johnpass", "employee")
    success, dept_obj = dept_manager.create_department_db("Sales", None)
    sales_dept_id = dept_obj.id

    # Log in as admin
    success, admin_token = auth_manager.login("admin", "admin")
    assert success is True
    admin_username = auth_manager.get_logged_in_user(admin_token)

    # Update john_doe to Manager and assign to Sales department
    success, msg = auth_manager.update_user_role(admin_username, "john_doe", "manager", sales_dept_id)
    assert success is True
    assert "Role for john_doe updated to manager and department set." in msg
    print(f"Update John Doe: {msg}")

    # Verify role and department
    all_users = auth_manager.get_all_users()
    john_doe_data = next((u for u in all_users if u['username'] == "john_doe"), None)
    assert john_doe_data is not None
    assert john_doe_data['role'] == "manager"
    assert john_doe_data['department_id'] == sales_dept_id
    print(f"Verified John Doe's role ({john_doe_data['role']}) and department ({john_doe_data['department_id']}).")

    # Correctly register 'another_admin' as an actual admin for the test
    db = SessionLocal()
    try:
        new_admin_user = User(username="another_admin", password_hash=hashlib.sha256("adminpass".encode()).hexdigest(), role="admin", department_id=None)
        db.add(new_admin_user)
        db.commit()
    finally:
        db.close()

    # Try to change another admin's role (should fail)
    success, msg = auth_manager.update_user_role(admin_username, "another_admin", "employee", None)
    assert success is False # This assertion should now pass
    assert "Cannot change the role of another admin." in msg
    print(f"Attempt to demote another admin: {msg}")

    # Try to set invalid role (should fail)
    success, msg = auth_manager.update_user_role(admin_username, "john_doe", "invalid_role", None)
    assert success is False
    assert "Invalid role." in msg
    print(f"Attempt to set invalid role: {msg}")

def test_token_validation_and_logout():
    print("\n--- Token Validation and Logout Test ---")
    auth_manager = AuthManager.get_instance()
    
    # Login admin
    success, admin_token = auth_manager.login("admin", "admin")
    assert success is True
    assert auth_manager.validate_token(admin_token) is True
    print("Admin token is valid after login.")

    # Logout admin
    success, msg = auth_manager.logout(admin_token)
    assert success is True
    assert "Logged out." in msg
    print(f"Logout: {msg}")

    # Verify token is no longer valid
    assert auth_manager.validate_token(admin_token) is False
    print("Admin token is invalid after logout.")
