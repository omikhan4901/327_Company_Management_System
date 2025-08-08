# payroll.py

from abc import ABC, abstractmethod
from datetime import datetime
import json
import os
import uuid


# Strategy Pattern
class SalaryStrategy(ABC):
    @abstractmethod
    def calculate_salary(self, base_salary, hours_worked, overtime_hours, **kwargs):
        pass


class DefaultSalaryStrategy(SalaryStrategy):
    def __init__(self, overtime_rate=1.5):
        self.overtime_rate = overtime_rate

    def calculate_salary(self, base_salary, hours_worked, overtime_hours, **kwargs):
        hourly_rate = base_salary / 160
        return round((hours_worked + overtime_hours * self.overtime_rate) * hourly_rate, 2)


class CommissionSalaryStrategy(SalaryStrategy):
    def __init__(self, commission_rate=0.1):
        self.commission_rate = commission_rate

    def calculate_salary(self, base_salary, hours_worked, overtime_hours, **kwargs):
        sales = kwargs.get("sales", 0)
        return round(base_salary + (sales * self.commission_rate), 2)


class PaySlip:
    def __init__(self, employee_id, base_salary, hours_worked, overtime_hours, month, year, salary, strategy_name):
        self.slip_id = str(uuid.uuid4())
        self.employee_id = employee_id
        self.base_salary = base_salary
        self.hours_worked = hours_worked
        self.overtime_hours = overtime_hours
        self.month = month
        self.year = year
        self.salary = salary
        self.strategy_name = strategy_name
        self.generated_at = datetime.now()

    def to_dict(self):
        return {
            "slip_id": self.slip_id,
            "employee_id": self.employee_id,
            "base_salary": self.base_salary,
            "hours_worked": self.hours_worked,
            "overtime_hours": self.overtime_hours,
            "salary": self.salary,
            "month": self.month,
            "year": self.year,
            "strategy": self.strategy_name,
            "generated_at": self.generated_at.strftime("%Y-%m-%d %H:%M:%S")
        }

    @staticmethod
    def from_dict(data):
        slip = PaySlip(
            employee_id=data["employee_id"],
            base_salary=data["base_salary"],
            hours_worked=data["hours_worked"],
            overtime_hours=data["overtime_hours"],
            month=data["month"],
            year=data["year"],
            salary=data["salary"],
            strategy_name=data["strategy"]
        )
        slip.slip_id = data["slip_id"]
        slip.generated_at = datetime.strptime(data["generated_at"], "%Y-%m-%d %H:%M:%S")
        return slip


class PayrollManager:
    def __init__(self, strategy=None, file_path="payroll.json", notifier=None):
        self.strategy = strategy or DefaultSalaryStrategy()
        self.file_path = file_path
        self.notifier = notifier
        self.slips = {}
        self._load_slips()

    def _load_slips(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                try:
                    data = json.load(f)
                    for slip_data in data:
                        slip = PaySlip.from_dict(slip_data)
                        self.slips[slip.slip_id] = slip
                except json.JSONDecodeError:
                    print("[ERROR] Failed to parse payroll.json.")

    def _save_slips(self):
        with open(self.file_path, "w") as f:
            json.dump([s.to_dict() for s in self.slips.values()], f, indent=4)

    def set_strategy(self, strategy: SalaryStrategy):
        self.strategy = strategy

    def generate_payslip(self, employee_id, base_salary, hours_worked, overtime_hours, month, year, **kwargs):
        salary = self.strategy.calculate_salary(base_salary, hours_worked, overtime_hours, **kwargs)
        slip = PaySlip(employee_id, base_salary, hours_worked, overtime_hours, month, year, salary, self.strategy.__class__.__name__)
        self.slips[slip.slip_id] = slip
        self._save_slips()

        if self.notifier:
            msg = f"Payslip for {month} {year} generated. Net salary: BDT {salary}"
            self.notifier.send_notification(msg, employee_id)

        return slip.to_dict()

    def get_payslips_by_employee(self, employee_id):
        return [s.to_dict() for s in self.slips.values() if s.employee_id == employee_id]

    def get_all_payslips(self):
        return [s.to_dict() for s in self.slips.values()]
