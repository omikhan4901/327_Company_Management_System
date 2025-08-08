from payroll import PayrollManager, DefaultSalaryStrategy, CommissionSalaryStrategy

def run_tests():
    pm = PayrollManager()

    print("\n--- Default Strategy (Base + OT) ---")
    payslip = pm.generate_payslip(
        employee_id="mohaimen",
        base_salary=50000,
        hours_worked=160,
        overtime_hours=5,
        month="August",
        year=2025
    )
    print(payslip)

    print("\n--- Commission Strategy (Sales-Based) ---")
    pm.set_strategy(CommissionSalaryStrategy(commission_rate=0.2))
    payslip2 = pm.generate_payslip(
        employee_id="john",
        base_salary=30000,
        hours_worked=160,
        overtime_hours=0,
        month="August",
        year=2025,
        sales=25000
    )
    print(payslip2)

    print("\n--- All PaySlips ---")
    for slip in pm.get_all_payslips():
        print(slip)

if __name__ == "__main__":
    run_tests()
