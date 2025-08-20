# main.py (example usage)

from task import Task
from user import User
from payroll import PayrollSystem, ExternalPayrollService, PayrollAdapter
from task_manager import TaskManager, RoundRobinStrategy, PriorityStrategy
from report_manager import ReportManager, CSVReportStrategy, PDFReportStrategy

# ----- Observer Example -----
task1 = Task(1, "Prepare report")
user1 = User("Alice")
user2 = User("Bob")

task1.register_observer(user1)
task1.register_observer(user2)
task1.set_status("Completed")

# ----- Adapter Example -----
payroll = PayrollSystem()
payroll.add_salary("emp1", 5000)
adapter = PayrollAdapter(payroll, ExternalPayrollService())
adapter.process_payment("emp1")

# ----- Strategy Example -----
tasks = ["T1", "T2", "T3"]
users = ["Alice", "Bob"]

manager = TaskManager(RoundRobinStrategy())
print(manager.assign_tasks(tasks, users))

manager.set_strategy(PriorityStrategy())
print(manager.assign_tasks([("T1", 3), ("T2", 1), ("T3", 2)], users))

report_data = {"revenue": 1000, "expenses": 500}
report_manager = ReportManager(CSVReportStrategy())
print(report_manager.generate_report(report_data))

report_manager.set_strategy(PDFReportStrategy())
print(report_manager.generate_report(report_data))
