# report_manager.py

from collections import defaultdict
from datetime import datetime
from database import SessionLocal, Task, Attendance, Payslip
from typing import List
class ReportManager:
    def __init__(self):
        pass # The constructor no longer needs to specify file paths.

    def get_task_report_by_employee(self):
        db = SessionLocal()
        try:
            tasks = db.query(Task).all()
            report = defaultdict(list)
            for task in tasks:
                report[task.assigned_to].append({
                    "title": task.title,
                    "status": task.status,
                    "deadline": task.deadline
                })
            return dict(report)
        finally:
            db.close()

    def get_task_status_summary(self):
        db = SessionLocal()
        try:
            tasks = db.query(Task).all()
            summary = defaultdict(int)
            for task in tasks:
                summary[task.status] += 1
            return dict(summary)
        finally:
            db.close()

    def get_total_hours_by_employee(self):
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

    def get_attendance_by_date(self, target_date):
        db = SessionLocal()
        try:
            entries = db.query(Attendance).filter(Attendance.date == target_date).all()
            return [
                {
                    "employee_id": e.employee_id,
                    "check_in": e.check_in,
                    "check_out": e.check_out
                } for e in entries
            ]
        finally:
            db.close()

    def get_payslips_by_employee(self):
        db = SessionLocal()
        try:
            slips = db.query(Payslip).all()
            report = defaultdict(list)
            for slip in slips:
                report[slip.employee_id].append({
                    "month": slip.month,
                    "year": slip.year,
                    "salary": slip.salary,
                    "strategy": slip.strategy
                })
            return dict(report)
        finally:
            db.close()

    def get_total_pay_by_employee(self):
        db = SessionLocal()
        try:
            slips = db.query(Payslip).all()
            totals = defaultdict(float)
            for slip in slips:
                totals[slip.employee_id] += slip.salary
            return dict(totals)
        finally:
            db.close()
    
    def get_task_report_by_department_ids(self, department_ids: List[int]):
        db = SessionLocal()
        try:
            # Get usernames associated with these department IDs
            from database import User # Import User model here to avoid circular dependency
            users_in_depts = db.query(User).filter(User.department_id.in_(department_ids)).all()
            usernames = [u.username for u in users_in_depts]

            if not usernames:
                return {} # No users in these departments

            tasks = db.query(Task).filter(Task.assigned_to.in_(usernames)).all()
            report = defaultdict(list)
            for task in tasks:
                report[task.assigned_to].append({
                    "title": task.title,
                    "status": task.status,
                    "deadline": task.deadline
                })
            return dict(report)
        finally:
            db.close()

    def get_total_hours_by_department_ids(self, department_ids: List[int]):
        db = SessionLocal()
        try:
            from database import User # Import User model here
            users_in_depts = db.query(User).filter(User.department_id.in_(department_ids)).all()
            usernames = [u.username for u in users_in_depts]

            if not usernames:
                return {}

            entries = db.query(Attendance).filter(Attendance.employee_id.in_(usernames)).all()
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

    def get_total_pay_by_department_ids(self, department_ids: List[int]):
        db = SessionLocal()
        try:
            from database import User # Import User model here
            users_in_depts = db.query(User).filter(User.department_id.in_(department_ids)).all()
            usernames = [u.username for u in users_in_depts]

            if not usernames:
                return {}

            slips = db.query(Payslip).filter(Payslip.employee_id.in_(usernames)).all()
            totals = defaultdict(float)
            for slip in slips:
                totals[slip.employee_id] += slip.salary
            return dict(totals)
        finally:
            db.close()