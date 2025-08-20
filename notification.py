# notification.py

from abc import ABC, abstractmethod
from datetime import datetime
import json
import os


class NotificationObserver(ABC):
    @abstractmethod
    def update(self, message: str, recipient: str):
        pass


class NotificationSubject:
    def __init__(self):
        self._observers = []

    def register_observer(self, observer: "NotificationObserver"):
        self._observers.append(observer)

    def remove_observer(self, observer: "NotificationObserver"):
        self._observers.remove(observer)

    def notify_all(self, message, recipient):
        for observer in self._observers:
            observer.update(message, recipient)


class InAppNotifier(NotificationObserver):
    def __init__(self, subject: NotificationSubject, log_file="notifications.json"):
        self.notifications = []
        self.log_file = log_file
        self._load_logs()
        subject.register_observer(self)   # auto-register

    def _load_logs(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    self.notifications = json.load(f)
                print(f"[INFO] Loaded {len(self.notifications)} stored notifications.")
            except json.JSONDecodeError:
                print("[ERROR] Failed to parse notifications.json.")

    def _save_logs(self):
        with open(self.log_file, "w") as f:
            json.dump(self.notifications, f, indent=4)

    def update(self, message, recipient):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "to": recipient,
            "message": message,
            "timestamp": timestamp
        }
        self.notifications.append(entry)
        self._save_logs()
        print(f"[In-App] ({recipient}) {message}")

    # Added method for compatibility with TaskManager and PayrollManager
    def send_notification(self, message, recipient):
        self.update(message, recipient)


class EmailNotifier(NotificationObserver):
    def __init__(self, subject: NotificationSubject):
        subject.register_observer(self)

    def _send_email(self, recipient, message):
        """Simulates sending an email via an external service."""
        print(f"--- [Email Service] Sending email to {recipient} ---")
        print(f"Subject: System Notification")
        print(f"Body: {message}")
        print("--------------------------------------------------")

    def update(self, message, recipient):
        # We will assume this calls a real email API
        self._send_email(recipient, message)


class NotificationManager:
    def __init__(self):
        self.subject = NotificationSubject()

    def send_notification(self, event_message, recipient):
        self.subject.notify_all(event_message, recipient)
