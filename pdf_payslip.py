# pdf_payslip.py

import io
from fpdf import FPDF
from datetime import datetime

class PDFPayslipGenerator:
    def __init__(self):
        pass

    def generate_payslip_pdf(self, payslip_data):
        """
        Generates a payslip PDF into an in-memory bytes stream.
        
        Args:
            payslip_data (dict): A dictionary containing payslip details.
        
        Returns:
            io.BytesIO: A BytesIO object containing the PDF content.
        """
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        
        # Company Header
        pdf.cell(0, 10, "Company Payslip", 0, 1, "C")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Generated: {payslip_data['generated_at']}", 0, 1, "C")
        pdf.ln(10)

        # Employee and Period Details
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Employee ID: {payslip_data['employee_id']}", 0, 1)
        pdf.cell(0, 10, f"Month: {payslip_data['month']} {payslip_data['year']}", 0, 1)
        pdf.ln(5)

        # Salary Breakdown
        pdf.set_font("Arial", "", 10)
        pdf.cell(50, 10, "Base Salary:", 0)
        pdf.cell(0, 10, f"BDT {payslip_data['base_salary']}", 0, 1)
        
        pdf.cell(50, 10, "Hours Worked:", 0)
        pdf.cell(0, 10, f"{payslip_data['hours_worked']} hours", 0, 1)
        
        pdf.cell(50, 10, "Overtime Hours:", 0)
        pdf.cell(0, 10, f"{payslip_data['overtime_hours']} hours", 0, 1)
        
        pdf.cell(50, 10, "Calculation Strategy:", 0)
        pdf.cell(0, 10, payslip_data['strategy'], 0, 1)
        
        # Net Salary
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "-----------------------------------", 0, 1, "C")
        pdf.cell(50, 10, "Net Salary:", 0)
        pdf.cell(0, 10, f"BDT {payslip_data['salary']}", 0, 1)

        # Output the PDF to a BytesIO object
        # 'S' returns as a string, then encode to bytes
        pdf_output_bytes = pdf.output(dest='S').encode('latin1') 
        return io.BytesIO(pdf_output_bytes) # Wrap in BytesIO for file-like object