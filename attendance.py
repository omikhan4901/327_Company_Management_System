import uuid
import os
import json
from datetime import datetime
from abc import ABC, abstractmethod
from database import SessionLocal, Attendance
from collections import defaultdict
from typing import Optional, List
# ----------------------
# Adapter Interface
# ----------------------

class AttendanceAdapter(ABC):
    @abstractmethod
    def get_hours_worked(self, employee_id):
        pass

# ----------------------
# Attendance Manager
# ----------------------

class AttendanceManager:
    def __init__(self, notifier=None):
        self.notifier = notifier

    def check_in(self, employee_id):
        db = SessionLocal()
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            current_time = datetime.now().strftime("%H:%M:%S")

            existing_entry = db.query(Attendance).filter(
                Attendance.employee_id == employee_id,
                Attendance.date == today
            ).first()

            if existing_entry:
                return False, "Already checked in today."

            new_entry = Attendance(
                employee_id=employee_id,
                date=today,
                check_in=current_time
            )
            db.add(new_entry)
            db.commit()

            if self.notifier:
                self.notifier.send_notification(f"Checked in at {current_time}", employee_id)

            return True, f"Check-in successful at {current_time}"
        finally:
            db.close()

    def check_out(self, employee_id):
        db = SessionLocal()
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            current_time = datetime.now().strftime("%H:%M:%S")

            entry = db.query(Attendance).filter(
                Attendance.employee_id == employee_id,
                Attendance.date == today,
                Attendance.check_out.is_(None)
            ).first()

            if not entry:
                return False, "No check-in found for today."

            entry.check_out = current_time
            db.commit()

            if self.notifier:
                self.notifier.send_notification(f"Checked out at {current_time}", employee_id)

            return True, f"Check-out successful at {current_time}"
        finally:
            db.close()

    def get_attendance_for_employee(self, employee_id):
        db = SessionLocal()
        try:
            records = db.query(Attendance).filter(Attendance.employee_id == employee_id).all()
            return [
                {
                    "date": r.date,
                    "check_in": r.check_in,
                    "check_out": r.check_out
                } for r in records
            ]
        finally:
            db.close()

    def get_total_hours_for_employee(self, employee_id):
        db = SessionLocal()
        try:
            records = db.query(Attendance).filter(Attendance.employee_id == employee_id).all()
            total_hours = 0
            for r in records:
                if r.check_in and r.check_out:
                    in_time = datetime.strptime(r.check_in, "%H:%M:%S")
                    out_time = datetime.strptime(r.check_out, "%H:%M:%S")
                    delta = out_time - in_time
                    total_hours += delta.total_seconds() / 3600
            return round(total_hours, 2)
        finally:
            db.close()

    def get_summary_by_date(self, date):
        db = SessionLocal()
        try:
            records = db.query(Attendance).filter(Attendance.date == date).all()
            return [
                {
                    "date": r.date,
                    "check_in": r.check_in,
                    "check_out": r.check_out
                } for r in records
            ]
        finally:
            db.close()
    def get_all_attendance_records(self):
        db = SessionLocal()
        try:
            records = db.query(Attendance).all()
            return records
        finally:
            db.close()

    def get_total_hours_for_all_employees(self):
        db = SessionLocal()
        try:
            entries = db.query(Attendance).all()
            totals = defaultdict(float)
            for e in entries:
                if e.check_in and e.check_out:
                    in_time = datetime.strptime(e.check_in, "%H:%M:%S")
                    out_time = datetime.strptime(e.check_out, "%H:%M:%S")
                    worked = round((out_time - in_time).total_seconds() / 3600, 2)
                    totals[e.employee_id] += worked
            return dict(totals)
        finally:
            db.close()
    def get_attendance_for_employees(self, employee_ids: List[str]):
        db = SessionLocal()
        try:
            records = db.query(Attendance).filter(Attendance.employee_id.in_(employee_ids)).all()
            return records
        finally:
            db.close()

    def get_total_hours_for_employees(self, employee_ids: List[str]):
        db = SessionLocal()
        try:
            records = db.query(Attendance).filter(Attendance.employee_id.in_(employee_ids)).all()
            totals = defaultdict(float)
            for r in records:
                if r.check_in and r.check_out:
                    in_time = datetime.strptime(r.check_in, "%H:%M:%S")
                    out_time = datetime.strptime(r.check_out, "%H:%M:%S")
                    worked = round((out_time - in_time).total_seconds() / 3600, 2)
                    totals[r.employee_id] += worked
            return dict(totals)
        finally:
            db.close()

# ----------------------
# Adapter Design Pattern
# ----------------------

class AttendanceManagerAdapter(AttendanceAdapter):
    def __init__(self, attendance_manager: AttendanceManager):
        self.attendance_manager = attendance_manager

    def get_hours_worked(self, employee_id):
        return self.attendance_manager.get_total_hours_for_employee(employee_id)