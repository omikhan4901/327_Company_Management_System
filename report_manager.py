# report_manager.py

import json
import os
from collections import defaultdict
from datetime import datetime


class ReportManager:
    def __init__(self, task_file="tasks.json", attendance_file="attendance.json", payroll_file="payroll.json"):
        self.task_file = task_file
        self.attendance_file = attendance_file
        self.payroll_file = payroll_file

    def get_task_report_by_employee(self):
        if not os.path.exists(self.task_file):
            return {}

        with open(self.task_file, "r") as f:
            tasks = json.load(f)

        report = defaultdict(list)
        for task in tasks:
            report[task["assigned_to"]].append({
                "title": task["title"],
                "status": task["status"],
                "deadline": task["deadline"]
            })

        return report

    def get_task_status_summary(self):
        if not os.path.exists(self.task_file):
            return {}

        with open(self.task_file, "r") as f:
            tasks = json.load(f)

        summary = defaultdict(int)
        for task in tasks:
            summary[task["status"]] += 1

        return dict(summary)

    def get_total_hours_by_employee(self):
        if not os.path.exists(self.attendance_file):
            return {}

        with open(self.attendance_file, "r") as f:
            entries = json.load(f)

        totals = defaultdict(float)
        for e in entries:
            check_in = e.get("check_in")
            check_out = e.get("check_out")
            if check_in and check_out:
                in_time = datetime.strptime(check_in, "%H:%M:%S")
                out_time = datetime.strptime(check_out, "%H:%M:%S")
                worked = round((out_time - in_time).total_seconds() / 3600, 2)
                totals[e["employee_id"]] += worked

        return dict(totals)

    def get_attendance_by_date(self, target_date):
        if not os.path.exists(self.attendance_file):
            return []

        with open(self.attendance_file, "r") as f:
            entries = json.load(f)

        return [e for e in entries if e["date"] == target_date]

    def get_payslips_by_employee(self):
        if not os.path.exists(self.payroll_file):
            return {}

        with open(self.payroll_file, "r") as f:
            slips = json.load(f)

        report = defaultdict(list)
        for slip in slips:
            report[slip["employee_id"]].append({
                "month": slip["month"],
                "year": slip["year"],
                "salary": slip["salary"],
                "strategy": slip["strategy"]
            })

        return report

    def get_total_pay_by_employee(self):
        if not os.path.exists(self.payroll_file):
            return {}

        with open(self.payroll_file, "r") as f:
            slips = json.load(f)

        totals = defaultdict(float)
        for slip in slips:
            totals[slip["employee_id"]] += slip["salary"]

        return dict(totals)
