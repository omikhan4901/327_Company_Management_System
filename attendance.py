# attendance.py

import uuid
import os
import json
from datetime import datetime
from abc import ABC, abstractmethod

# ----------------------
# Adapter Interface
# ----------------------

class AttendanceAdapter(ABC):
    @abstractmethod
    def get_hours_worked(self, employee_id):
        pass

# ----------------------
# Attendance Entry
# ----------------------

class AttendanceEntry:
    def __init__(self, employee_id, date, check_in=None, check_out=None):
        self.id = str(uuid.uuid4())
        self.employee_id = employee_id
        self.date = date
        self.check_in = check_in
        self.check_out = check_out

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "date": self.date,
            "check_in": self.check_in,
            "check_out": self.check_out
        }

    @staticmethod
    def from_dict(data):
        return AttendanceEntry(
            employee_id=data["employee_id"],
            date=data["date"],
            check_in=data.get("check_in"),
            check_out=data.get("check_out")
        )

    def hours_worked(self):
        if not self.check_in or not self.check_out:
            return 0
        in_time = datetime.strptime(self.check_in, "%H:%M:%S")
        out_time = datetime.strptime(self.check_out, "%H:%M:%S")
        delta = out_time - in_time
        return round(delta.total_seconds() / 3600, 2)

# ----------------------
# Attendance Manager
# ----------------------

class AttendanceManager:
    def __init__(self, file_path="attendance.json", notifier=None):
        self.file_path = file_path
        self.entries = {}
        self.notifier = notifier
        self._load_entries()

    def _load_entries(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                try:
                    data = json.load(f)
                    for entry_data in data:
                        entry = AttendanceEntry.from_dict(entry_data)
                        self.entries[entry.id] = entry
                except json.JSONDecodeError:
                    print("[ERROR] Failed to parse attendance.json.")

    def _save_entries(self):
        with open(self.file_path, "w") as f:
            json.dump([e.to_dict() for e in self.entries.values()], f, indent=4)

    def check_in(self, employee_id):
        today = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")

        for entry in self.entries.values():
            if entry.employee_id == employee_id and entry.date == today:
                return False, "Already checked in today."

        entry = AttendanceEntry(employee_id, today, check_in=current_time)
        self.entries[entry.id] = entry
        self._save_entries()

        if self.notifier:
            self.notifier.send_notification(f"Checked in at {current_time}", employee_id)

        return True, f"Check-in successful at {current_time}"

    def check_out(self, employee_id):
        today = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")

        for entry in self.entries.values():
            if entry.employee_id == employee_id and entry.date == today:
                if entry.check_out:
                    return False, "Already checked out today."
                entry.check_out = current_time
                self._save_entries()

                if self.notifier:
                    self.notifier.send_notification(f"Checked out at {current_time}", employee_id)

                return True, f"Check-out successful at {current_time}"

        return False, "No check-in found for today."

    def get_attendance_for_employee(self, employee_id):
        return [e.to_dict() for e in self.entries.values() if e.employee_id == employee_id]

    def get_total_hours_for_employee(self, employee_id):
        return sum(e.hours_worked() for e in self.entries.values() if e.employee_id == employee_id)

    def get_summary_by_date(self, date):
        return [e.to_dict() for e in self.entries.values() if e.date == date]

# ----------------------
# Adapter Implementation
# ----------------------

class DefaultAttendanceAdapter(AttendanceAdapter):
    def __init__(self, attendance_manager: AttendanceManager):
        self.attendance_manager = attendance_manager

    def get_hours_worked(self, employee_id):
        return self.attendance_manager.get_total_hours_for_employee(employee_id)
