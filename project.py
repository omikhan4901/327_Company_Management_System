import json
import os
from datetime import datetime
from threading import Lock
from authentication import AuthManager

class Project:
    """
    Represents a project in the system with project data and management capabilities.
    Integrates with authentication for access control.
    """
    
    _instance = None
    _lock = Lock()
    _projects_file = "projects.json"
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Project, cls).__new__(cls)
                cls._instance.projects = {}
                cls._instance._load_projects_from_file()
        return cls._instance
    
    def _load_projects_from_file(self):
        """Load projects data from JSON file."""
        if os.path.exists(self._projects_file):
            with open(self._projects_file, "r") as f:
                try:
                    self.projects = json.load(f)
                    print(f"[INFO] Loaded {len(self.projects)} projects from {self._projects_file}")
                except json.JSONDecodeError:
                    print("[ERROR] Failed to decode projects file. Starting with empty project list.")
        else:
            print("[INFO] No projects file found. Starting fresh.")
    
    def _save_projects_to_file(self):
        """Save projects data to JSON file."""
        with open(self._projects_file, "w") as f:
            json.dump(self.projects, f, indent=4)
        print(f"[INFO] Saved {len(self.projects)} projects to {self._projects_file}")
    
    def create_project(self, token, project_name, description, datapoints=None):
        """Create a new project with authentication check."""
        auth = AuthManager()
        if not auth.validate_token(token):
            return False, "Invalid authentication token"
        
        if project_name in self.projects:
            return False, "Project name already exists"
        
        user_role = auth.get_user_role(token)
        if user_role != "Admin":
            return False, "Only Admins can create projects"
        
        self.projects[project_name] = {
            "description": description,
            "created_by": auth.get_logged_in_user(token),
            "created_at": datetime.now().isoformat(),
            "datapoints": datapoints if datapoints else [],
            "status": "active"
        }
        
        self._save_projects_to_file()
        return True, "Project created successfully"
    
    def add_datapoints(self, token, project_name, datapoints):
        """Add datapoints to an existing project."""
        auth = AuthManager()
        if not auth.validate_token(token):
            return False, "Invalid authentication token"
        
        if project_name not in self.projects:
            return False, "Project not found"
        
        user_role = auth.get_user_role(token)
        if user_role not in ["Admin", "Employee"]:
            return False, "Insufficient permissions"
        
        if not isinstance(datapoints, list):
            return False, "Datapoints must be provided as a list"
        
        self.projects[project_name]["datapoints"].extend(datapoints)
        self._save_projects_to_file()
        return True, "Datapoints added successfully"
    
    def get_project(self, token, project_name):
        """Retrieve project details with authentication check."""
        auth = AuthManager()
        if not auth.validate_token(token):
            return False, "Invalid authentication token"
        
        if project_name not in self.projects:
            return False, "Project not found"
        
        return True, self.projects[project_name]
    
    def list_projects(self, token):
        """List all projects with authentication check."""
        auth = AuthManager()
        if not auth.validate_token(token):
            return False, "Invalid authentication token"
        
        return True, list(self.projects.keys())
    
    def generate_report(self, token, project_name, report_type="full"):
        """Generate a report for a project with different compilation options."""
        auth = AuthManager()
        if not auth.validate_token(token):
            return False, "Invalid authentication token"
        
        if project_name not in self.projects:
            return False, "Project not found"
        
        project = self.projects[project_name]
        
        if report_type == "full":
            report = {
                "project_name": project_name,
                "description": project["description"],
                "created_by": project["created_by"],
                "created_at": project["created_at"],
                "datapoints_count": len(project["datapoints"]),
                "status": project["status"],
                "datapoints_sample": project["datapoints"][:5] if project["datapoints"] else []
            }
        elif report_type == "partial":
            report = {
                "project_name": project_name,
                "datapoints_count": len(project["datapoints"]),
                "status": project["status"]
            }
        else:
            return False, "Invalid report type"
        
        return True, report