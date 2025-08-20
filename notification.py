# notification.py

from abc import ABC, abstractmethod
from datetime import datetime
import json
import os

class NotificationObserver(ABC):
    @abstractmethod
    def update(self, message: str, recipient: str):
        pass


class InAppNotifier(NotificationObserver):
    def __init__(self, log_file="notifications.json"):
        self.notifications = []
        self.log_file = log_file
        self._load_logs()

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


class EmailNotifier(NotificationObserver):
    def update(self, message, recipient):
        print(f"[Email] To: {recipient} | {message}")


class NotificationSubject:
    def __init__(self):
        self._observers = []

    def register_observer(self, observer: NotificationObserver):
        self._observers.append(observer)

    def remove_observer(self, observer: NotificationObserver):
        self._observers.remove(observer)

    def notify_all(self, message, recipient):
        for observer in self._observers:
            observer.update(message, recipient)


class NotificationManager:
    def __init__(self):
        self.subject = NotificationSubject()

    def add_notifier(self, notifier: NotificationObserver):
        self.subject.register_observer(notifier)

    def remove_notifier(self, notifier: NotificationObserver):
        self.subject.remove_observer(notifier)

    def send_notification(self, event_message, recipient):
        self.subject.notify_all(event_message, recipient)
