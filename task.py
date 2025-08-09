import json
import os
from datetime import datetime
from threading import Lock
from abc import ABC, abstractmethod
from authentication import AuthManager

class TaskComponent(ABC):
    """Abstract base class for Task components"""
    @abstractmethod
    def get_details(self):
        pass

    @abstractmethod
    def to_dict(self):
        pass

class ConcreteTask(TaskComponent):
    """Concrete implementation of a basic Task"""
    def __init__(self, title, description, creator):
        self.title = title
        self.description = description
        self.creator = creator
        self.created_at = datetime.now().isoformat()
        self.status = "Pending"
        self.assignee = None
        self.due_date = None

    def get_details(self):
        return {
            "title": self.title,
            "description": self.description,
            "creator": self.creator,
            "created_at": self.created_at,
            "status": self.status,
            "assignee": self.assignee,
            "due_date": self.due_date
        }

    def to_dict(self):
        return self.get_details()

class TaskDecorator(TaskComponent):
    """Base decorator class"""
    def __init__(self, task_component):
        self._task_component = task_component

    def get_details(self):
        return self._task_component.get_details()

    def to_dict(self):
        return self._task_component.to_dict()

class PriorityDecorator(TaskDecorator):
    """Adds priority to a task"""
    def __init__(self, task_component, priority="Medium"):
        super().__init__(task_component)
        self.priority = priority

    def get_details(self):
        details = super().get_details()
        details["priority"] = self.priority
        return details

class LabelDecorator(TaskDecorator):
    """Adds labels to a task"""
    def __init__(self, task_component, labels=None):
        super().__init__(task_component)
        self.labels = labels if labels else []

    def get_details(self):
        details = super().get_details()
        details["labels"] = self.labels
        return details

class AttachmentDecorator(TaskDecorator):
    """Adds attachments to a task"""
    def __init__(self, task_component, attachments=None):
        super().__init__(task_component)
        self.attachments = attachments if attachments else []

    def get_details(self):
        details = super().get_details()
        details["attachments"] = self.attachments
        return details

class TaskManager:
    """Manages tasks with persistence"""
    _instance = None
    _lock = Lock()
    _tasks_file = "tasks.json"

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TaskManager, cls).__new__(cls)
                cls._instance.tasks = {}
                cls._instance._load_tasks_from_file()
        return cls._instance

    def _load_tasks_from_file(self):
        """Load tasks from JSON file"""
        if os.path.exists(self._tasks_file):
            with open(self._tasks_file, "r") as f:
                try:
                    data = json.load(f)
                    self.tasks = {task_id: self._deserialize_task(task_data) 
                                for task_id, task_data in data.items()}
                    print(f"[INFO] Loaded {len(self.tasks)} tasks from {self._tasks_file}")
                except json.JSONDecodeError:
                    print("[ERROR] Failed to decode tasks file. Starting with empty task list.")
        else:
            print("[INFO] No tasks file found. Starting fresh.")

    def _deserialize_task(self, task_data):
        """Reconstruct a task from serialized data"""
        base_task = ConcreteTask(
            title=task_data["title"],
            description=task_data["description"],
            creator=task_data["creator"]
        )
        base_task.status = task_data["status"]
        base_task.assignee = task_data.get("assignee")
        base_task.due_date = task_data.get("due_date")

        task = base_task
        
        if "priority" in task_data:
            task = PriorityDecorator(task, task_data["priority"])
        
        if "labels" in task_data:
            task = LabelDecorator(task, task_data["labels"])
        
        if "attachments" in task_data:
            task = AttachmentDecorator(task, task_data["attachments"])
        
        return task

    def _save_tasks_to_file(self):
        """Save tasks to JSON file"""
        data = {task_id: task.to_dict() for task_id, task in self.tasks.items()}
        with open(self._tasks_file, "w") as f:
            json.dump(data, f, indent=4)
        print(f"[INFO] Saved {len(self.tasks)} tasks to {self._tasks_file}")

    def create_task(self, token, title, description):
        """Create a new basic task"""
        auth = AuthManager()
        if not auth.validate_token(token):
            return False, "Invalid authentication token"
        
        creator = auth.get_logged_in_user(token)
        if not creator:
            return False, "User not found"
        
        task_id = str(len(self.tasks) + 1)
        self.tasks[task_id] = ConcreteTask(title, description, creator)
        self._save_tasks_to_file()
        return True, task_id

    def decorate_task(self, token, task_id, decorator_type, **kwargs):
        """Add a decorator to an existing task"""
        auth = AuthManager()
        if not auth.validate_token(token):
            return False, "Invalid authentication token"
        
        if task_id not in self.tasks:
            return False, "Task not found"
        
        task = self.tasks[task_id]
        
        if decorator_type == "priority":
            if "priority" not in kwargs:
                return False, "Priority not specified"
            self.tasks[task_id] = PriorityDecorator(task, kwargs["priority"])
        elif decorator_type == "labels":
            self.tasks[task_id] = LabelDecorator(task, kwargs.get("labels"))
        elif decorator_type == "attachments":
            self.tasks[task_id] = AttachmentDecorator(task, kwargs.get("attachments"))
        else:
            return False, "Invalid decorator type"
        
        self._save_tasks_to_file()
        return True, "Task decorated successfully"

    def update_task_status(self, token, task_id, status):
        """Update a task's basic status"""
        auth = AuthManager()
        if not auth.validate_token(token):
            return False, "Invalid authentication token"
        
        if task_id not in self.tasks:
            return False, "Task not found"
        
        # Get the innermost task (might be decorated)
        task = self.tasks[task_id]
        while isinstance(task, TaskDecorator):
            task = task._task_component
        
        task.status = status
        self._save_tasks_to_file()
        return True, "Task status updated"

    def get_task(self, token, task_id):
        """Retrieve task details"""
        auth = AuthManager()
        if not auth.validate_token(token):
            return False, "Invalid authentication token"
        
        if task_id not in self.tasks:
            return False, "Task not found"
        
        return True, self.tasks[task_id].get_details()

    def list_tasks(self, token):
        """List all tasks"""
        auth = AuthManager()
        if not auth.validate_token(token):
            return False, "Invalid authentication token"
        
        return True, {task_id: task.get_details() for task_id, task in self.tasks.items()}