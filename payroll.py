# payroll.py

from abc import ABC, abstractmethod
from datetime import datetime
import json
import os
import uuid
from database import SessionLocal, Payslip
from typing import Any, Tuple, List # Import Tuple and Any for type hints

# Strategy Pattern
class Strategy(ABC):
    @abstractmethod
    def execute(self, base_salary, hours_worked, overtime_hours, **kwargs):
        pass


class ConcreteStrategyA(Strategy):  # Default Salary Strategy
    def __init__(self, overtime_rate=1.5):
        self.overtime_rate = overtime_rate
        self.name = "Standard Hourly Pay"

    def execute(self, base_salary, hours_worked, overtime_hours, **kwargs):
        hourly_rate = base_salary / 160
        return round((hours_worked + overtime_hours * self.overtime_rate) * hourly_rate, 2)


class ConcreteStrategyB(Strategy):  # Commission Salary Strategy
    def __init__(self, commission_rate=0.1):
        self.commission_rate = commission_rate
        self.name = "Sales Commission Pay"

    def execute(self, base_salary, hours_worked, overtime_hours, **kwargs):
        sales = kwargs.get("sales", 0)
        return round(base_salary + (sales * self.commission_rate), 2)


# Context
class PayrollManager:
    def __init__(self, strategy=None, notifier=None):
        self.strategy = strategy or ConcreteStrategyA()
        self.notifier = notifier
        self.slips = {}

    def set_strategy(self, strategy: Strategy):
        self.strategy = strategy

    def generate_payslip(self, employee_id, base_salary, hours_worked, overtime_hours, month, year, **kwargs) -> Tuple[bool, Any]:
        db = SessionLocal()
        try:
            salary = self.strategy.execute(base_salary, hours_worked, overtime_hours, **kwargs)
            
            new_slip = Payslip(
                employee_id=employee_id,
                base_salary=base_salary,
                hours_worked=hours_worked,
                overtime_hours=overtime_hours,
                month=month,
                year=year,
                salary=salary,
                strategy=self.strategy.name
            )

            db.add(new_slip)
            db.commit()
            db.refresh(new_slip) # Refresh to get the generated ID and timestamp

            if self.notifier:
                msg = f"Payslip for {month} {year} generated. Net salary: BDT {salary}"
                self.notifier.send_notification(msg, employee_id)
            
            # Return success status and the payslip data as a dictionary
            return True, {
                "slip_id": new_slip.id,
                "employee_id": new_slip.employee_id,
                "base_salary": new_slip.base_salary,
                "hours_worked": new_slip.hours_worked,
                "overtime_hours": new_slip.overtime_hours,
                "salary": new_slip.salary,
                "month": new_slip.month,
                "year": new_slip.year,
                "strategy": new_slip.strategy,
                "generated_at": new_slip.generated_at.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            db.rollback() # Rollback changes in case of an error
            print(f"Error generating payslip in PayrollManager: {e}")
            # Return failure status and the error message
            return False, str(e)
        finally:
            db.close()

    def get_payslips_by_employee(self, employee_id):
        db = SessionLocal()
        try:
            slips = db.query(Payslip).filter(Payslip.employee_id == employee_id).all()
            return [
                {
                    "slip_id": s.id,
                    "employee_id": s.employee_id,
                    "base_salary": s.base_salary,
                    "hours_worked": s.hours_worked,
                    "overtime_hours": s.overtime_hours,
                    "salary": s.salary,
                    "month": s.month,
                    "year": s.year,
                    "strategy": s.strategy,
                    "generated_at": s.generated_at.strftime("%Y-%m-%d %H:%M:%S")
                } for s in slips
            ]
        finally:
            db.close()

    def get_all_payslips(self):
        db = SessionLocal()
        try:
            slips = db.query(Payslip).all()
            return [
                {
                    "slip_id": s.id,
                    "employee_id": s.employee_id,
                    "base_salary": s.base_salary,
                    "hours_worked": s.hours_worked,
                    "overtime_hours": s.overtime_hours,
                    "salary": s.salary,
                    "month": s.month,
                    "year": s.year,
                    "strategy": s.strategy,
                    "generated_at": s.generated_at.strftime("%Y-%m-%d %H:%M:%S")
                } for s in slips
            ]
        finally:
            db.close()
    
    def get_payslip_by_id(self, payslip_id):
        db = SessionLocal()
        try:
            slip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
            if slip:
                return {
                    "slip_id": slip.id,
                    "employee_id": slip.employee_id,
                    "base_salary": slip.base_salary,
                    "hours_worked": slip.hours_worked,
                    "overtime_hours": slip.overtime_hours,
                    "salary": slip.salary,
                    "month": slip.month,
                    "year": slip.year,
                    "strategy": slip.strategy,
                    "generated_at": slip.generated_at.strftime("%Y-%m-%d %H:%M:%S")
                }
            return None
        finally:
            db.close()

    def get_payslips_by_employees(self, employee_ids: List[str]):
        db = SessionLocal()
        try:
            slips = db.query(Payslip).filter(Payslip.employee_id.in_(employee_ids)).all()
            return [
                {
                    "slip_id": s.id,
                    "employee_id": s.employee_id,
                    "base_salary": s.base_salary,
                    "hours_worked": s.hours_worked,
                    "overtime_hours": s.overtime_hours,
                    "salary": s.salary,
                    "month": s.month,
                    "year": s.year,
                    "strategy": s.strategy,
                    "generated_at": s.generated_at.strftime("%Y-%m-%d %H:%M:%S")
                } for s in slips
            ]
        finally:
            db.close()