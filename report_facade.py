# report_facade.py

from report_manager import ReportManager


# --- Subsystems ---
class TaskReport:
    def get_by_employee(self, report_manager, employee_id):
        return report_manager.get_task_report_by_employee().get(employee_id, [])


class PayslipReport:
    def get_by_employee(self, report_manager, employee_id):
        return report_manager.get_payslips_by_employee().get(employee_id, [])


class HoursReport:
    def get_by_employee(self, report_manager, employee_id):
        return report_manager.get_total_hours_by_employee().get(employee_id, 0)


class PayReport:
    def get_by_employee(self, report_manager, employee_id):
        return report_manager.get_total_pay_by_employee().get(employee_id, 0)


class SystemReport:
    def get_task_status_summary(self, report_manager):
        return report_manager.get_task_status_summary()

    def get_total_hours(self, report_manager):
        return report_manager.get_total_hours_by_employee()

    def get_total_pay(self, report_manager):
        return report_manager.get_total_pay_by_employee()


# --- Facade ---
class ReportFacade:
    def __init__(self):
        self.report_manager = ReportManager()
        self.task_report = TaskReport()
        self.payslip_report = PayslipReport()
        self.hours_report = HoursReport()
        self.pay_report = PayReport()
        self.system_report = SystemReport()

    def get_employee_summary(self, employee_id):
        tasks = self.task_report.get_by_employee(self.report_manager, employee_id)
        payslips = self.payslip_report.get_by_employee(self.report_manager, employee_id)
        hours = self.hours_report.get_by_employee(self.report_manager, employee_id)
        pay = self.pay_report.get_by_employee(self.report_manager, employee_id)

        return {
            "tasks": tasks,
            "payslips": payslips,
            "total_hours": hours,
            "total_pay": pay
        }

    def get_system_summary(self):
        return {
            "task_status_summary": self.system_report.get_task_status_summary(self.report_manager),
            "total_hours_by_employee": self.system_report.get_total_hours(self.report_manager),
            "total_pay_by_employee": self.system_report.get_total_pay(self.report_manager),
        }


# --- Client Code Example ---
if __name__ == "__main__":
    facade = ReportFacade()

    print("\n--- Employee Summary ---")
    print(facade.get_employee_summary("emp123"))

    print("\n--- System Summary ---")
    print(facade.get_system_summary())
