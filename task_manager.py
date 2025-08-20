from enum import Enum
import uuid
from datetime import datetime
from abc import ABC, abstractmethod
from database import SessionLocal, Task
from typing import List
class TaskStatus(Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"

# ---------------- Base Task Class ----------------
class TaskModel:
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
            "type": self.__class__.__name__
        }

# ---------------- Specialized Task Types ----------------
class HighPriorityTask(TaskModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.priority = "High"


class DeadlineSensitiveTask(TaskModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        return TaskModel(title, description, assigned_to, deadline, status, task_id, created_at)


class HighPriorityTaskCreator(TaskCreator):
    def factory_method(self, title, description, assigned_to, deadline, status, task_id, created_at):
        return HighPriorityTask(title, description, assigned_to, deadline, status, task_id, created_at)


class DeadlineSensitiveTaskCreator(TaskCreator):
    def factory_method(self, title, description, assigned_to, deadline, status, task_id, created_at):
        return DeadlineSensitiveTask(title, description, assigned_to, deadline, status, task_id, created_at)


# ---------------- Task Manager ----------------
class TaskManager:
    def __init__(self, notifier=None):
        self.notifier = notifier
    
    def _create_task_from_db(self, db_task):
        """Helper to convert a DB object to a TaskModel instance."""
        creator = TaskCreator.get_creator(db_task.type)
        return creator.create_task(
            title=db_task.title,
            description=db_task.description,
            assigned_to=db_task.assigned_to,
            deadline=db_task.deadline,
            status=TaskStatus(db_task.status),
            task_id=db_task.id,
            created_at=db_task.created_at
        )

    def create_task(self, title, description, assigned_to, deadline, task_type="Task"):
        db = SessionLocal()
        try:
            db_task = Task(
                title=title,
                description=description,
                assigned_to=assigned_to,
                deadline=deadline,
                status=TaskStatus.NOT_STARTED.value
            )
            db.add(db_task)
            db.commit()
            db.refresh(db_task)

            if self.notifier:
                msg = f"You've been assigned a new {task_type}: '{db_task.title}' (Deadline: {db_task.deadline})"
                self.notifier.send_notification(msg, assigned_to)
            
            return db_task.id
        finally:
            db.close()

    def update_task_status(self, task_id, new_status_str):
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return False, "Task not found"
            try:
                task.status = TaskStatus(new_status_str).value
            except ValueError:
                return False, "Invalid status"
            db.commit()
            return True, "Status updated"
        finally:
            db.close()

    def get_task_by_id(self, task_id):
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                return {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "assigned_to": task.assigned_to,
                    "deadline": task.deadline,
                    "status": task.status,
                    "created_at": task.created_at.strftime("%Y-%m-%d %H:%M:%S")
                }
            return None
        finally:
            db.close()

    def get_tasks_by_user(self, username):
        db = SessionLocal()
        try:
            tasks = db.query(Task).filter(Task.assigned_to == username).all()
            return [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "assigned_to": t.assigned_to,
                    "deadline": t.deadline,
                    "status": t.status,
                    "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S")
                } for t in tasks
            ]
        finally:
            db.close()

    def get_all_tasks(self):
        db = SessionLocal()
        try:
            tasks = db.query(Task).all()
            return [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "assigned_to": t.assigned_to,
                    "deadline": t.deadline,
                    "status": t.status,
                    "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S")
                } for t in tasks
            ]
        finally:
            db.close()
    def get_tasks_for_employees(self, employee_ids: List[str]):
        db = SessionLocal()
        try:
            tasks = db.query(Task).filter(Task.assigned_to.in_(employee_ids)).all()
            return [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "assigned_to": t.assigned_to,
                    "deadline": t.deadline,
                    "status": t.status,
                    "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S")
                } for t in tasks
            ]
        finally:
            db.close()