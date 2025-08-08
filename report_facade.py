# report_facade.py

from report_manager import ReportManager


class ReportFacade:
    def __init__(self):
        self.report_manager = ReportManager()

    def get_employee_summary(self, employee_id):
        task_report = self.report_manager.get_task_report_by_employee().get(employee_id, [])
        payslips = self.report_manager.get_payslips_by_employee().get(employee_id, [])
        total_hours = self.report_manager.get_total_hours_by_employee().get(employee_id, 0)
        total_pay = self.report_manager.get_total_pay_by_employee().get(employee_id, 0)

        return {
            "tasks": task_report,
            "payslips": payslips,
            "total_hours": total_hours,
            "total_pay": total_pay
        }

    def get_system_summary(self):
        return {
            "task_status_summary": self.report_manager.get_task_status_summary(),
            "total_hours_by_employee": self.report_manager.get_total_hours_by_employee(),
            "total_pay_by_employee": self.report_manager.get_total_pay_by_employee()
        }
