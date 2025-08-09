from user import UserManager
from authentication import AuthManager
import os

def run_tests():
    # Setup authentication first
    auth = AuthManager()
    auth.register_user("test_admin", "adminpass", "Admin")
    auth.register_user("test_employee", "emppass", "Employee")
    auth.register_user("test_viewer", "viewpass", "Viewer")
    
    # Get tokens
    _, admin_token = auth.login("test_admin", "adminpass")
    _, emp_token = auth.login("test_employee", "emppass")
    _, viewer_token = auth.login("test_viewer", "viewpass")
    
    user_manager = UserManager()
    
    print("\n--- User Profile Creation Tests ---")
    print(user_manager.create_user_profile("invalid_token", "new", "New User", "new@test.com"))  # invalid token
    print(user_manager.create_user_profile(emp_token, "new", "New User", "new@test.com"))  # employee trying to create
    print(user_manager.create_user_profile(admin_token, "new_user", "New User", "new@test.com", "Employee"))  # valid
    print(user_manager.create_user_profile(admin_token, "new_user", "Duplicate", "dup@test.com"))  # duplicate
    print(user_manager.create_user_profile(admin_token, "invalid_role", "Invalid Role", "role@test.com", "InvalidRole"))  # bad role
    
    print("\n--- User Profile Update Tests ---")
    print(user_manager.update_user_profile("invalid_token", "new_user", {"full_name": "Updated"}))  # invalid token
    print(user_manager.update_user_profile(emp_token, "new_user", {"full_name": "Updated"}))  # wrong user
    print(user_manager.update_user_profile(emp_token, "test_employee", {"full_name": "Employee Updated"}))  # self-update
    print(user_manager.update_user_profile(admin_token, "new_user", {"full_name": "Admin Updated"}))  # admin update
    print(user_manager.update_user_profile(admin_token, "new_user", {"role": "Viewer"}))  # role update
    print(user_manager.update_user_profile(admin_token, "new_user", {"invalid_field": "value"}))  # invalid field
    
    print("\n--- User Profile Retrieval Tests ---")
    print(user_manager.get_user_profile("invalid_token", "new_user"))  # invalid token
    print(user_manager.get_user_profile(emp_token, "new_user"))  # unauthorized
    print(user_manager.get_user_profile(emp_token, "test_employee"))  # self
    print(user_manager.get_user_profile(admin_token, "test_employee"))  # admin
    
    print("\n--- User Listing Tests ---")
    print(user_manager.list_users("invalid_token"))  # invalid token
    print(user_manager.list_users(emp_token))  # unauthorized
    print(user_manager.list_users(admin_token))  # admin
    
    print("\n--- User Activation Tests ---")
    print(user_manager.deactivate_user("invalid_token", "new_user"))  # invalid token
    print(user_manager.deactivate_user(emp_token, "new_user"))  # unauthorized
    print(user_manager.deactivate_user(admin_token, "new_user"))  # admin
    print(user_manager.activate_user(admin_token, "new_user"))  # admin
    
    # Cleanup test files
    if os.path.exists("user_profiles.json"):
        os.remove("user_profiles.json")
    if os.path.exists("users.json"):
        os.remove("users.json")

if __name__ == "__main__":
    run_tests()