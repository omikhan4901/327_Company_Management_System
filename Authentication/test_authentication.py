# test/test_authentication.py

from authentication import AuthManager

def run_tests():
    auth = AuthManager()

    print("\n--- Register Users ---")
    print(auth.register_user("admin2", "pass789", "Admin"))
    print(auth.register_user("Mohaimen", "abc789", "Employee"))
    print(auth.register_user("admin", "anotherpass", "Admin"))  # duplicate

    print("\n--- Login Users ---")
    success, result = auth.login("admin", "pass123")
    print("Admin login:", success, result)
    admin_token = result if success else None

    success, result = auth.login("john", "wrongpass")
    print("John login (wrong pw):", success, result)

    print("\n--- Token Validation ---")
    print("Is token valid?", auth.validate_token(admin_token))

    print("\n--- Get User Role ---")
    print("Admin role:", auth.get_user_role(admin_token))

    print("\n--- Logout ---")
    print("Logout result:", auth.logout(admin_token))
    print("Is token still valid?", auth.validate_token(admin_token))

if __name__ == "__main__":
    run_tests()

