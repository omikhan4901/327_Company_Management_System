# authentication.py

import hashlib
import uuid
import json
import os
from threading import Lock


class User:
    """
    Represents a user in the system with username, password hash, and role.
    """
    def __init__(self, username, password_hash, role):
        self.username = username
        self.password_hash = password_hash
        self.role = role

    def check_password(self, password):
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()

    def to_dict(self):
        return {
            "password_hash": self.password_hash,
            "role": self.role
        }

    @staticmethod
    def from_dict(username, data):
        return User(username, data["password_hash"], data["role"])


class AuthManager:
    """
    Singleton class to manage user authentication and session tokens.
    Supports file-based persistence for user storage.
    """

    _instance = None
    _lock = Lock()
    _user_file = "users.json"

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AuthManager, cls).__new__(cls)
                cls._instance.users = {}
                cls._instance.sessions = {}
                cls._instance._load_users_from_file()
        return cls._instance

    def _load_users_from_file(self):
        """
        Loads user data from a JSON file.
        """
        if os.path.exists(self._user_file):
            with open(self._user_file, "r") as f:
                try:
                    data = json.load(f)
                    self.users = {
                        username: User.from_dict(username, udata)
                        for username, udata in data.items()
                    }
                    print(f"[INFO] Loaded {len(self.users)} users from {self._user_file}")
                except json.JSONDecodeError:
                    print("[ERROR] Failed to decode user file. Starting with empty user list.")
        else:
            print("[INFO] No user file found. Starting fresh.")

    def _save_users_to_file(self):
        """
        Saves user data to a JSON file.
        """
        data = {username: user.to_dict() for username, user in self.users.items()}
        with open(self._user_file, "w") as f:
            json.dump(data, f, indent=4)
        print(f"[INFO] Saved {len(self.users)} users to {self._user_file}")

    def register_user(self, username, password, role):
        if username in self.users:
            return False, "User already exists."
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.users[username] = User(username, password_hash, role)
        self._save_users_to_file()
        return True, "User registered successfully."

    def login(self, username, password):
        user = self.users.get(username)
        if not user:
            return False, "User not found."
        if not user.check_password(password):
            return False, "Invalid password."

        token = str(uuid.uuid4())
        self.sessions[token] = username
        return True, token

    def logout(self, token):
        if token in self.sessions:
            del self.sessions[token]
            return True, "Logged out."
        return False, "Invalid token."

    def validate_token(self, token):
        return token in self.sessions

    def get_user_role(self, token):
        username = self.sessions.get(token)
        if username and username in self.users:
            return self.users[username].role
        return None

    def get_logged_in_user(self, token):
        return self.sessions.get(token)
