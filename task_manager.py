from enum import Enum
import uuid
from datetime import datetime
import json
import os
from abc import ABC, abstractmethod


class TaskStatus(Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


# ---------------- Base Task Class ----------------
class Task:
    def __init__(self, title, description, assigned_to, deadline, status=TaskStatus.NOT_STARTED, task_id=None, created_at=None):
        self.task_id = task_id or str(uuid.uuid4())
        self.title = title
        self.description = description
        self.assigned_to = assigned_to
        self.deadline = deadline
        self.status = status
        self.created_at = created_at or datetime.now()

    def update_status(self, new_status: TaskStatus):
        if not isinstance(new_status, TaskStatus):
            raise ValueError("Invalid status")
        self.status = new_status

    def to_dict(self):
        return {
            "id": self.task_id,
            "title": self.title,
            "description": self.description,
            "assigned_to": self.assigned_to,
            "deadline": self.deadline,
            "status": self.status.value,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "type": self.__class__.__name__  # include type for factory reconstruction
        }

    @staticmethod
    def from_dict(data):
        # Delegate creation to TaskCreator subclasses
        task_type = data.get("type", "Task")
        creator = TaskCreator.get_creator(task_type)
        return creator.create_task(
            title=data["title"],
            description=data["description"],
            assigned_to=data["assigned_to"],
            deadline=data["deadline"],
            status=TaskStatus(data["status"]),
            task_id=data["id"],
            created_at=datetime.strptime(data["created_at"], "%Y-%m-%d %H:%M:%S")
        )


# ---------------- Specialized Task Types ----------------
class HighPriorityTask(Task):
    def __init__(self, title, description, assigned_to, deadline, status=TaskStatus.NOT_STARTED, task_id=None, created_at=None):
        super().__init__(title, description, assigned_to, deadline, status, task_id, created_at)
        self.priority = "High"


class DeadlineSensitiveTask(Task):
    def __init__(self, title, description, assigned_to, deadline, status=TaskStatus.NOT_STARTED, task_id=None, created_at=None):
        super().__init__(title, description, assigned_to, deadline, status, task_id, created_at)
        self.priority = "Deadline-Sensitive"


# ---------------- Factory Method Pattern ----------------
class TaskCreator(ABC):
    @abstractmethod
    def factory_method(self, title, description, assigned_to, deadline, status, task_id, created_at):
        pass

    def create_task(self, title, description, assigned_to, deadline, status=TaskStatus.NOT_STARTED, task_id=None, created_at=None):
        return self.factory_method(title, description, assigned_to, deadline, status, task_id, created_at)

    @staticmethod
    def get_creator(task_type: str):
        if task_type == "Task":
            return BaseTaskCreator()
        elif task_type == "HighPriorityTask":
            return HighPriorityTaskCreator()
        elif task_type == "DeadlineSensitiveTask":
            return DeadlineSensitiveTaskCreator()
        else:
            raise ValueError(f"Unknown task type: {task_type}")


class BaseTaskCreator(TaskCreator):
    def factory_method(self, title, description, assigned_to, deadline, status, task_id, created_at):
        return Task(title, description, assigned_to, deadline, status, task_id, created_at)


class HighPriorityTaskCreator(TaskCreator):
    def factory_method(self, title, description, assigned_to, deadline, status, task_id, created_at):
        return HighPriorityTask(title, description, assigned_to, deadline, status, task_id, created_at)


class DeadlineSensitiveTaskCreator(TaskCreator):
    def factory_method(self, title, description, assigned_to, deadline, status, task_id, created_at):
        return DeadlineSensitiveTask(title, description, assigned_to, deadline, status, task_id, created_at)


# ---------------- Task Manager ----------------
class TaskManager:
    def __init__(self, file_path="tasks.json", notifier=None):
        self.file_path = file_path
        self.notifier = notifier
        self.tasks = {}
        self._load_tasks_from_file()

    def _load_tasks_from_file(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                try:
                    data = json.load(f)
                    for task_data in data:
                        task = Task.from_dict(task_data)
                        self.tasks[task.task_id] = task
                except json.JSONDecodeError:
                    print("[ERROR] Failed to parse tasks.json.")

    def _save_tasks_to_file(self):
        data = [task.to_dict() for task in self.tasks.values()]
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4)

    def create_task(self, title, description, assigned_to, deadline, task_type="Task"):
        creator = TaskCreator.get_creator(task_type)
        task = creator.create_task(title, description, assigned_to, deadline)
        self.tasks[task.task_id] = task
        self._save_tasks_to_file()

        if self.notifier:
            msg = f"You've been assigned a new {task_type}: '{task.title}' (Deadline: {task.deadline})"
            self.notifier.send_notification(msg, assigned_to)

        return task.task_id

    def update_task_status(self, task_id, new_status_str):
        task = self.tasks.get(task_id)
        if not task:
            return False, "Task not found"
        try:
            new_status = TaskStatus(new_status_str)
        except ValueError:
            return False, "Invalid status"
        task.update_status(new_status)
        self._save_tasks_to_file()
        return True, "Status updated"

    def get_task_by_id(self, task_id):
        task = self.tasks.get(task_id)
        return task.to_dict() if task else None

    def get_tasks_by_user(self, username):
        return [task.to_dict() for task in self.tasks.values() if task.assigned_to == username]

    def get_all_tasks(self):
        return [task.to_dict() for task in self.tasks.values()]
