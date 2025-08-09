from task import TaskManager, ConcreteTask, PriorityDecorator, LabelDecorator, AttachmentDecorator
from authentication import AuthManager
import os

def run_tests():
    # Setup authentication first
    auth = AuthManager()
    auth.register_user("task_admin", "adminpass", "Admin")
    auth.register_user("task_user", "userpass", "Employee")
    
    # Get tokens
    _, admin_token = auth.login("task_admin", "adminpass")
    _, user_token = auth.login("task_user", "userpass")
    
    task_manager = TaskManager()
    
    print("\n--- Task Creation Tests ---")
    print(task_manager.create_task("invalid_token", "Test", "Description"))  # invalid token
    print(task_manager.create_task(user_token, "User Task", "Created by regular user"))  # valid
    print(task_manager.create_task(admin_token, "Admin Task", "Created by admin"))  # valid
    _, task_id = task_manager.create_task(user_token, "Decorated Task", "Will be decorated")
    
    print("\n--- Task Decoration Tests ---")
    print(task_manager.decorate_task("invalid_token", task_id, "priority", priority="High"))  # invalid token
    print(task_manager.decorate_task(user_token, "invalid_id", "priority", priority="High"))  # invalid task
    print(task_manager.decorate_task(user_token, task_id, "invalid_type"))  # invalid decorator
    print(task_manager.decorate_task(user_token, task_id, "priority", priority="High"))  # valid priority
    print(task_manager.decorate_task(user_token, task_id, "labels", labels=["urgent", "backend"]))  # valid labels
    print(task_manager.decorate_task(user_token, task_id, "attachments", attachments=["file1.pdf"]))  # valid attachments
    
    print("\n--- Task Status Update Tests ---")
    print(task_manager.update_task_status("invalid_token", task_id, "In Progress"))  # invalid token
    print(task_manager.update_task_status(user_token, "invalid_id", "In Progress"))  # invalid task
    print(task_manager.update_task_status(user_token, task_id, "In Progress"))  # valid update
    
    print("\n--- Task Retrieval Tests ---")
    print(task_manager.get_task("invalid_token", task_id))  # invalid token
    print(task_manager.get_task(user_token, "invalid_id"))  # invalid task
    print(task_manager.get_task(user_token, task_id))  # valid
    
    print("\n--- Task Listing Tests ---")
    print(task_manager.list_tasks("invalid_token"))  # invalid token
    print(task_manager.list_tasks(user_token))  # valid
    
    # Test direct decorator functionality
    print("\n--- Direct Decorator Tests ---")
    base_task = ConcreteTask("Direct Task", "Testing decorators directly", "test")
    print("Base task:", base_task.get_details())
    
    prioritized = PriorityDecorator(base_task, "High")
    print("With priority:", prioritized.get_details())
    
    labeled = LabelDecorator(prioritized, ["test", "decorator"])
    print("With labels:", labeled.get_details())
    
    full_task = AttachmentDecorator(labeled, ["image.png"])
    print("Fully decorated:", full_task.get_details())
    
    # Cleanup test files
    if os.path.exists("tasks.json"):
        os.remove("tasks.json")
    if os.path.exists("users.json"):
        os.remove("users.json")

if __name__ == "__main__":
    run_tests()