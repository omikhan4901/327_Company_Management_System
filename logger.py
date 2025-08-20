# logger.py
import json
import os
from datetime import datetime
from threading import Lock

class Logger:
    """
    Singleton class for logging system events and user actions.
    """
    __instance = None
    __lock = Lock()
    _log_file = "audit.log"

    def __init__(self):
        if Logger.__instance is not None:
            raise Exception("This class is a singleton! Use get_instance().")
        self.logs = []
        self._load_logs()

    @staticmethod
    def get_instance():
        if Logger.__instance is None:
            with Logger.__lock:
                if Logger.__instance is None:
                    Logger.__instance = Logger()
        return Logger.__instance

    def _load_logs(self):
        if os.path.exists(self._log_file):
            with open(self._log_file, "r") as f:
                self.logs = [json.loads(line) for line in f]

    def _save_log(self, entry):
        with open(self._log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def log_event(self, username, action, details=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "username": username,
            "action": action,
            "details": details or {}
        }
        self.logs.append(log_entry)
        self._save_log(log_entry)
        print(f"[LOG] {username} | {action} | {details}")
    
    def get_logs(self):
        return self.logs