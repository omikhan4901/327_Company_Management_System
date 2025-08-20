# test_department_management.py

import os
import pytest
import time # Added for time.sleep
from department_manager import DepartmentManager
from database import create_tables, SessionLocal, Department, User, engine # Import engine and User
from authentication import AuthManager # For default admin creation
import hashlib # For password hashing in user creation

# Helper function to clean up database
@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    # Helper to force-delete the database file, with retries
    def force_delete_db():
        SessionLocal.remove()
        engine.dispose() # Dispose of the engine to release file lock
        if os.path.exists("company.db"):
            for i in range(5):
                try:
                    os.remove("company.db")
                    break
                except PermissionError as e:
                    print(f"Failed to delete DB, retrying... ({i+1}/5)")
                    time.sleep(0.1)
                    if i == 4:
                        raise e
    
    # --- Setup Phase ---
    force_delete_db()
    create_tables()
    
    # Create default admin and department for tests that need them
    auth_manager = AuthManager.get_instance()
    auth_manager.create_default_admin()
    dept_manager = DepartmentManager()
    dept_manager.create_default_department()

    yield
    # --- Teardown Phase ---
    force_delete_db()

def test_create_default_department():
    print("\n--- Default Department Creation Test ---")
    # Fixture already creates it, just verify
    db = SessionLocal()
    try:
        default_dept = db.query(Department).filter(Department.name == "Unassigned").first()
        assert default_dept is not None
        assert default_dept.name == "Unassigned"
        assert default_dept.parent_department_id is None
        print(f"Default department '{default_dept.name}' created successfully.")
    finally:
        db.close()
 