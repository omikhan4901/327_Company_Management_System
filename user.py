import json
import os
from datetime import datetime
from threading import Lock
from authentication import AuthManager

class UserManager:
    """
    Comprehensive user management system with extended user profiles and management capabilities.
    Integrates with the authentication system but provides more extensive user management features.
    """
    
    _instance = None
    _lock = Lock()
    _user_profiles_file = "user_profiles.json"
    ROLES = ["Admin", "Employee", "Viewer"]
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(UserManager, cls).__new__(cls)
                cls._instance.user_profiles = {}
                cls._instance._load_user_profiles_from_file()
        return cls._instance
    
    def _load_user_profiles_from_file(self):
        """Load user profiles from JSON file."""
        if os.path.exists(self._user_profiles_file):
            with open(self._user_profiles_file, "r") as f:
                try:
                    self.user_profiles = json.load(f)
                    print(f"[INFO] Loaded {len(self.user_profiles)} user profiles from {self._user_profiles_file}")
                except json.JSONDecodeError:
                    print("[ERROR] Failed to decode user profiles file. Starting with empty profiles.")
        else:
            print("[INFO] No user profiles file found. Starting fresh.")
    
    def _save_user_profiles_to_file(self):
        """Save user profiles to JSON file."""
        with open(self._user_profiles_file, "w") as f:
            json.dump(self.user_profiles, f, indent=4)
        print(f"[INFO] Saved {len(self.user_profiles)} user profiles to {self._user_profiles_file}")
    
    def create_user_profile(self, token, username, full_name, email, role="Employee"):
        """
        Create a new user profile with extended information.
        Requires admin privileges.
        """
        auth = AuthManager()
        if not auth.validate_token(token):
            return False, "Invalid authentication token"
        
        if auth.get_user_role(token) != "Admin":
            return False, "Only Admins can create user profiles"
        
        if username in self.user_profiles:
            return False, "Username already exists"
        
        if role not in self.ROLES:
            return False, f"Invalid role. Must be one of: {', '.join(self.ROLES)}"
        
        self.user_profiles[username] = {
            "full_name": full_name,
            "email": email,
            "role": role,
            "created_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "is_active": True,
            "metadata": {}
        }
        
        self._save_user_profiles_to_file()
        return True, "User profile created successfully"
    
    def update_user_profile(self, token, username, updates):
        """
        Update an existing user profile.
        Users can update their own profile, admins can update any profile.
        """
        auth = AuthManager()
        if not auth.validate_token(token):
            return False, "Invalid authentication token"
        
        if username not in self.user_profiles:
            return False, "User not found"
        
        current_user = auth.get_logged_in_user(token)
        current_role = auth.get_user_role(token)
        
        # Users can only update their own profile unless they're admin
        if current_user != username and current_role != "Admin":
            return False, "You can only update your own profile"
        
        valid_fields = ["full_name", "email", "metadata"]
        if current_role == "Admin":
            valid_fields.append("role")
            valid_fields.append("is_active")
        
        for field, value in updates.items():
            if field in valid_fields:
                if field == "role" and value not in self.ROLES:
                    return False, f"Invalid role. Must be one of: {', '.join(self.ROLES)}"
                self.user_profiles[username][field] = value
            else:
                return False, f"Cannot update field: {field}"
        
        self.user_profiles[username]["last_modified"] = datetime.now().isoformat()
        self._save_user_profiles_to_file()
        return True, "User profile updated successfully"
    
    def get_user_profile(self, token, username):
        """
        Retrieve a user profile.
        Users can view their own profile, admins can view any profile.
        """
        auth = AuthManager()
        if not auth.validate_token(token):
            return False, "Invalid authentication token"
        
        if username not in self.user_profiles:
            return False, "User not found"
        
        current_user = auth.get_logged_in_user(token)
        current_role = auth.get_user_role(token)
        
        if current_user != username and current_role != "Admin":
            return False, "You can only view your own profile"
        
        return True, self.user_profiles[username]
    
    def list_users(self, token, active_only=True):
        """
        List all users with basic information.
        Requires admin privileges.
        """
        auth = AuthManager()
        if not auth.validate_token(token):
            return False, "Invalid authentication token"
        
        if auth.get_user_role(token) != "Admin":
            return False, "Only Admins can list users"
        
        users = []
        for username, profile in self.user_profiles.items():
            if not active_only or profile["is_active"]:
                users.append({
                    "username": username,
                    "full_name": profile["full_name"],
                    "role": profile["role"],
                    "email": profile["email"],
                    "is_active": profile["is_active"]
                })
        
        return True, users
    
    def deactivate_user(self, token, username):
        """
        Deactivate a user account.
        Requires admin privileges.
        """
        return self._set_user_active_status(token, username, False)
    
    def activate_user(self, token, username):
        """
        Activate a user account.
        Requires admin privileges.
        """
        return self._set_user_active_status(token, username, True)
    
    def _set_user_active_status(self, token, username, status):
        auth = AuthManager()
        if not auth.validate_token(token):
            return False, "Invalid authentication token"
        
        if auth.get_user_role(token) != "Admin":
            return False, "Only Admins can modify user status"
        
        if username not in self.user_profiles:
            return False, "User not found"
        
        self.user_profiles[username]["is_active"] = status
        self.user_profiles[username]["last_modified"] = datetime.now().isoformat()
        self._save_user_profiles_to_file()
        return True, f"User {'activated' if status else 'deactivated'} successfully"
    # user.py
from notification import Observer

class User(Observer):
    def __init__(self, name):
        self.name = name

    def update(self, message: str):
        print(f"[NOTIFICATION for {self.name}] {message}")
