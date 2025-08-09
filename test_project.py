from project import Project
from authentication import AuthManager
import os

def run_tests():
    # Setup authentication first
    auth = AuthManager()
    auth.register_user("test_admin", "adminpass", "Admin")
    auth.register_user("test_employee", "emppass", "Employee")
    
    # Get tokens
    _, admin_token = auth.login("test_admin", "adminpass")
    _, emp_token = auth.login("test_employee", "emppass")
    
    project = Project()
    
    print("\n--- Project Creation Tests ---")
    print(project.create_project("invalid_token", "test", "description"))  # invalid token
    print(project.create_project(emp_token, "test", "description"))  # employee trying to create
    print(project.create_project(admin_token, "test_project", "Test Description"))  # valid creation
    print(project.create_project(admin_token, "test_project", "Duplicate"))  # duplicate
    
    print("\n--- Datapoints Tests ---")
    print(project.add_datapoints("invalid_token", "test_project", [1, 2, 3]))  # invalid token
    print(project.add_datapoints(admin_token, "nonexistent", [1, 2, 3]))  # bad project
    print(project.add_datapoints(admin_token, "test_project", "not a list"))  # bad datapoints
    print(project.add_datapoints(admin_token, "test_project", [4, 5, 6]))  # valid add
    print(project.add_datapoints(emp_token, "test_project", [7, 8, 9]))  # employee adding
    
    print("\n--- Project Retrieval Tests ---")
    print(project.get_project("invalid_token", "test_project"))  # invalid token
    print(project.get_project(admin_token, "nonexistent"))  # bad project
    print(project.get_project(admin_token, "test_project"))  # valid
    
    print("\n--- Report Generation Tests ---")
    print(project.generate_report(admin_token, "test_project", "full"))
    print(project.generate_report(admin_token, "test_project", "partial"))
    print(project.generate_report(admin_token, "test_project", "invalid_type"))
    
    # Cleanup test files
    if os.path.exists("projects.json"):
        os.remove("projects.json")
    if os.path.exists("users.json"):
        os.remove("users.json")

if __name__ == "__main__":
    run_tests()