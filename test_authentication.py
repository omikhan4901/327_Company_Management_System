# test/test_authentication.py

import os
from authentication import AuthManager

def run_tests():
    # Reset user file for clean testing
    if os.path.exists("users.json"):
        os.remove("users.json")

    # Get singleton instances
    auth1 = AuthManager.get_instance()
    auth2 = AuthManager.get_instance()

    print("\n--- Singleton Test ---")
    print("auth1 is auth2?", auth1 is auth2)  # should be True

    print("\n--- Register Users ---")
    print(auth1.register_user("admin", "pass123", "Admin"))       # Admin with matching password
    print(auth1.register_user("Mohaimen", "abc789", "Employee"))  # Another user
    print(auth1.register_user("admin2", "pass789", "Admin"))      # Another admin

    print("\n--- Login Users ---")
    success, result = auth2.login("admin", "pass123")  # Should succeed
    print("Admin login:", success, result)
    admin_token = result if success else None

    success, result = auth2.login("john", "wrongpass")  # Nonexistent user
    print("John login (wrong pw):", success, result)

    print("\n--- Token Validation ---")
    print("Is token valid?", auth1.validate_token(admin_token))  # Should be True

    print("\n--- Get User Role ---")
    print("Admin role:", auth2.get_user_role(admin_token))  # Should return "Admin"

    print("\n--- Logout ---")
    print("Logout result:", auth1.logout(admin_token))  # Should succeed
    print("Is token still valid?", auth2.validate_token(admin_token))  # Should be False

if __name__ == "__main__":
    run_tests()
