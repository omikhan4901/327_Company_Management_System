# pdf_report.py

from fpdf import FPDF
from datetime import datetime
from report_manager import ReportManager

class PDFReportGenerator:
    def __init__(self):
        self.report_manager = ReportManager()

    def generate_task_report_pdf(self, filename="task_report.pdf"):
        # Get report data
        task_report = self.report_manager.get_task_report_by_employee()
        
        # Setup PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Employee Task Report", 0, 1, "C")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, "C")
        pdf.ln(10)

        # Loop through employees and their tasks
        for employee, tasks in task_report.items():
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, f"Employee: {employee}", 0, 1)
            pdf.set_font("Arial", "B", 10)
            pdf.cell(50, 10, "Title", 1)
            pdf.cell(50, 10, "Status", 1)
            pdf.cell(50, 10, "Deadline", 1)
            pdf.ln()

            pdf.set_font("Arial", "", 10)
            if not tasks:
                pdf.cell(150, 10, "No tasks found.", 1, 1)
            else:
                for task in tasks:
                    pdf.cell(50, 10, task.get("title", ""), 1)
                    pdf.cell(50, 10, task.get("status", ""), 1)
                    pdf.cell(50, 10, task.get("deadline", ""), 1)
                    pdf.ln()
            pdf.ln(5)

        pdf.output(filename)
        return filename