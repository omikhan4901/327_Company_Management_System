# test_task_management.py

import os
import pytest
import time # Added for time.sleep
from task_manager import TaskManager, TaskStatus
from database import create_tables, SessionLocal, Task, engine, Department, User # <-- Added Department, User, and engine
from notification import NotificationManager, InAppNotifier # For notifier integration
from authentication import AuthManager # For user setup in department test
from department_manager import DepartmentManager # For department setup in department test
import hashlib # For password hashing in user setup

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

def test_task_creation_and_retrieval():
    print("\n--- Task Creation and Retrieval Test ---")
    notifier = NotificationManager()
    in_app_notifier = InAppNotifier(notifier.subject) # To capture notifications
    tm = TaskManager(notifier=notifier)

    # Create a base task
    task_id1 = tm.create_task(
        title="Develop Feature X",
        description="Implement user authentication module.",
        assigned_to="alice",
        deadline="2025-09-01",
        task_type="Task"
    )
    assert task_id1 is not None
    print(f"Created Task 1 (ID: {task_id1})")

    # Create a high priority task
    task_id2 = tm.create_task(
        title="Fix Production Bug",
        description="Resolve critical login issue.",
        assigned_to="bob",
        deadline="2025-08-25",
        task_type="HighPriorityTask"
    )
    assert task_id2 is not None
    print(f"Created Task 2 (ID: {task_id2})")

    # Retrieve task by ID
    task1_data = tm.get_task_by_id(task_id1)
    assert task1_data is not None
    assert task1_data['title'] == "Develop Feature X"
    assert task1_data['status'] == TaskStatus.NOT_STARTED.value
    print(f"Retrieved Task 1: {task1_data['title']}, Status: {task1_data['status']}")

    # Retrieve tasks by user
    alice_tasks = tm.get_tasks_by_user("alice")
    assert len(alice_tasks) == 1
    assert alice_tasks[0]['title'] == "Develop Feature X"
    print(f"Tasks for Alice: {[t['title'] for t in alice_tasks]}")

    bob_tasks = tm.get_tasks_by_user("bob")
    assert len(bob_tasks) == 1
    assert bob_tasks[0]['title'] == "Fix Production Bug"
    print(f"Tasks for Bob: {[t['title'] for t in bob_tasks]}")

    # Get all tasks
    all_tasks = tm.get_all_tasks()
    assert len(all_tasks) == 2
    print(f"All tasks: {[t['title'] for t in all_tasks]}")

    # Check notification sent
    assert any(f"You've been assigned a new Task: 'Develop Feature X'" in n['message'] for n in in_app_notifier.notifications if n['to'] == 'alice')
    assert any(f"You've been assigned a new HighPriorityTask: 'Fix Production Bug'" in n['message'] for n in in_app_notifier.notifications if n['to'] == 'bob')
    print("Notifications verified for task assignment.")

def test_task_status_update():
    print("\n--- Task Status Update Test ---")
    tm = TaskManager()

    task_id = tm.create_task("Review Code", "Review pull request #123", "charlie", "2025-08-28")
    print(f"Created task (ID: {task_id}) for Charlie.")

    # Update status to In Progress
    success, msg = tm.update_task_status(task_id, TaskStatus.IN_PROGRESS.value)
    assert success is True
    assert "Status updated" in msg
    print(f"Updated status to In Progress: {msg}")

    updated_task = tm.get_task_by_id(task_id)
    assert updated_task['status'] == TaskStatus.IN_PROGRESS.value
    print(f"Verified updated status: {updated_task['status']}")

    # Update status to Completed
    success, msg = tm.update_task_status(task_id, TaskStatus.COMPLETED.value)
    assert success is True
    print(f"Updated status to Completed: {msg}")

    final_task = tm.get_task_by_id(task_id)
    assert final_task['status'] == TaskStatus.COMPLETED.value
    print(f"Verified final status: {final_task['status']}")

    # Try to update non-existent task
    success, msg = tm.update_task_status("non_existent_id", "Completed")
    assert success is False
    assert "Task not found" in msg
    print(f"Attempt to update non-existent task: {msg}")

    # Try to update with invalid status string
    success, msg = tm.update_task_status(task_id, "InvalidStatus")
    assert success is False
    assert "Invalid status" in msg
    print(f"Attempt to update with invalid status: {msg}")

def test_get_tasks_for_employees_by_department():
    print("\n--- Get Tasks for Employees by Department Test ---")
    auth_manager = AuthManager.get_instance()
    dept_manager = DepartmentManager()
    tm = TaskManager()

    # Create departments
    db_session = SessionLocal() # Use a session for initial department creation
    try:
        dev_dept_obj = Department(name="Development", parent_department_id=None)
        qa_dept_obj = Department(name="QA", parent_department_id=None)
        db_session.add_all([dev_dept_obj, qa_dept_obj])
        db_session.commit()
        db_session.refresh(dev_dept_obj)
        db_session.refresh(qa_dept_obj)
        dev_dept_id = dev_dept_obj.id
        qa_dept_id = qa_dept_obj.id
    finally:
        db_session.close()

    # Create users and assign to departments
    db_session = SessionLocal() # Use a fresh session for user creation
    try:
        db_session.add(User(username="dev_alice", password_hash=hashlib.sha256("pass".encode()).hexdigest(), role="employee", department_id=dev_dept_id))
        db_session.add(User(username="qa_bob", password_hash=hashlib.sha256("pass".encode()).hexdigest(), role="employee", department_id=qa_dept_id))
        db_session.add(User(username="dev_charlie", password_hash=hashlib.sha256("pass".encode()).hexdigest(), role="employee", department_id=dev_dept_id))
        db_session.commit()
    finally:
        db_session.close()

    # Create tasks
    tm.create_task("Code Module A", "Desc A", "dev_alice", "2025-09-01")
    tm.create_task("Test Module B", "Desc B", "qa_bob", "2025-09-05")
    tm.create_task("Refactor Code", "Desc C", "dev_charlie", "2025-09-10")
    tm.create_task("Review Tests", "Desc D", "dev_alice", "2025-09-15")

    # Get all users in Development department hierarchy
    dev_dept_ids = dept_manager.get_all_department_ids_in_hierarchy(dev_dept_id)
    dev_users = auth_manager.get_users_by_department_ids(dev_dept_ids)
    dev_usernames = [u["username"] for u in dev_users]
    print(f"Dev department users: {dev_usernames}")

    # Get tasks for Development department employees
    dev_tasks = tm.get_tasks_for_employees(dev_usernames)
    assert len(dev_tasks) == 3
    assert all(t['assigned_to'] in ["dev_alice", "dev_charlie"] for t in dev_tasks)
    print(f"Tasks for Dev department: {[t['title'] for t in dev_tasks]}")

    # Get all users in QA department hierarchy
    qa_dept_ids = dept_manager.get_all_department_ids_in_hierarchy(qa_dept_id)
    qa_users = auth_manager.get_users_by_department_ids(qa_dept_ids)
    qa_usernames = [u["username"] for u in qa_users]
    print(f"QA department users: {qa_usernames}")

    # Get tasks for QA department employees
    qa_tasks = tm.get_tasks_for_employees(qa_usernames)
    assert len(qa_tasks) == 1
    assert qa_tasks[0]['assigned_to'] == "qa_bob"
    print(f"Tasks for QA department: {[t['title'] for t in qa_tasks]}")
