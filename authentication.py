# authentication.py

import hashlib
import uuid
import os
from threading import Lock
import uuid
from database import SessionLocal, User
from typing import Optional, List

class AuthManager:
    __instance = None
    __lock = Lock()
    
    def __init__(self):
        if AuthManager.__instance is not None:
            raise Exception("This class is a singleton! Use get_instance().")
        self.sessions = {}

    @staticmethod
    def get_instance():
        with AuthManager.__lock:
            if AuthManager.__instance is None:
                AuthManager.__instance = AuthManager()
            return AuthManager.__instance

    def _get_user(self, db, username):
        return db.query(User).filter(User.username == username).first()

    def register_user(self, username, password, role):
        db = SessionLocal()
        try:
            if self._get_user(db, username):
                return False, "User already exists."
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            fixed_role = "employee"  # New users are always employees
            new_user = User(username=username, password_hash=password_hash, role=fixed_role)
            db.add(new_user)
            db.commit()
            return True, "User registered successfully."
        finally:
            db.close()

    def login(self, username, password):
        db = SessionLocal()
        try:
            user = self._get_user(db, username)
            if not user:
                return False, "User not found."
            if user.password_hash != hashlib.sha256(password.encode()).hexdigest():
                return False, "Invalid password."

            token = str(uuid.uuid4())
            self.sessions[token] = username
            return True, token
        finally:
            db.close()

    def logout(self, token):
        if token in self.sessions:
            del self.sessions[token]
            return True, "Logged out."
        return False, "Invalid token."

    def validate_token(self, token):
        return token in self.sessions

    def get_user_role(self, token):
        username = self.sessions.get(token)
        if username:
            db = SessionLocal()
            try:
                user = self._get_user(db, username)
                return user.role if user else None
            finally:
                db.close()
        return None
    
    def get_logged_in_user(self, token):
        return self.sessions.get(token)

    def update_user_role(self, admin_username, target_username, new_role, new_department_id=None): # <-- Corrected signature
        """Allows an admin to change a user's role and department, with restrictions."""
        db = SessionLocal()
        try:
            valid_roles = ["employee", "manager", "admin"]
            if new_role not in valid_roles:
                return False, "Invalid role."
            
            target_user = self._get_user(db, target_username)
            if not target_user:
                return False, "User not found."

            # Admin cannot change another admin's role
            if target_user.role == "admin" and target_user.username != admin_username:
                return False, "Cannot change the role of another admin."
            
            target_user.role = new_role
            target_user.department_id = new_department_id # <-- Ensure this line is present
            
            db.commit()
            return True, f"Role for {target_username} updated to {new_role} and department set."
        finally:
            db.close()

    def get_all_users(self):
        db = SessionLocal()
        try:
            users = db.query(User).all()
            return [{"username": u.username, "role": u.role, "department_id": u.department_id} for u in users]
        finally:
            db.close()
    def create_default_admin(self):
        db = SessionLocal()
        try:
            admin_user = db.query(User).filter(User.role == "admin").first()
            if not admin_user:
                # No admin user exists, create one
                username = "admin"
                password_hash = hashlib.sha256("admin".encode()).hexdigest()  # Default password is "admin"
                new_admin = User(username=username, password_hash=password_hash, role="admin")
                db.add(new_admin)
                db.commit()
                print("Default admin user 'admin' created with password 'admin'.")
        finally:
            db.close()
    def get_users_by_department_ids(self, department_ids: List[int]):
        db = SessionLocal()
        try:
            users = db.query(User).filter(User.department_id.in_(department_ids)).all()
            return [{"username": u.username, "role": u.role, "department_id": u.department_id} for u in users]
        finally:
            db.close()