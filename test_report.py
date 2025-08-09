from report import ReportManager, ReportFactory, FullReport, PartialReport, VisualReport
from authentication import AuthManager
import os

def run_tests():
    # Setup authentication first
    auth = AuthManager()
    auth.register_user("report_admin", "adminpass", "Admin")
    auth.register_user("report_user", "userpass", "Employee")
    
    # Get tokens
    _, admin_token = auth.login("report_admin", "adminpass")
    _, user_token = auth.login("report_user", "userpass")
    
    report_manager = ReportManager()
    sample_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    print("\n--- Report Generation Tests ---")
    print(report_manager.generate_report("invalid_token", "full", "Test", sample_data))  # invalid token
    print(report_manager.generate_report(user_token, "invalid_type", "Test", sample_data))  # invalid type
    print(report_manager.generate_report(user_token, "full", "Full Report", sample_data))  # valid full
    print(report_manager.generate_report(user_token, "partial", "Partial Report", sample_data))  # valid partial
    print(report_manager.generate_report(admin_token, "visual", "Visual Report", sample_data, chart_type="pie"))  # valid visual with param
    
    print("\n--- Report Retrieval Tests ---")
    _, report_id = report_manager.generate_report(user_token, "full", "Another Full", sample_data)
    print(report_manager.get_report("invalid_token", report_id))  # invalid token
    print(report_manager.get_report(user_token, "invalid_id"))  # invalid id
    print(report_manager.get_report(user_token, report_id))  # valid
    
    print("\n--- Report Listing Tests ---")
    print(report_manager.list_reports("invalid_token"))  # invalid token
    print(report_manager.list_reports(user_token))  # valid
    
    print("\n--- Direct Factory Tests ---")
    full = ReportFactory.create_report("full", "Direct Full", "tester", sample_data)
    print("Full report:", full.generate())
    
    partial = ReportFactory.create_report("partial", "Direct Partial", "tester", sample_data)
    print("Partial report:", partial.generate())
    
    visual = ReportFactory.create_report("visual", "Direct Visual", "tester", sample_data, chart_type="line")
    print("Visual report:", visual.generate())
    
    try:
        ReportFactory.create_report("invalid", "Bad", "tester", sample_data)
    except ValueError as e:
        print("Invalid report type error:", e)
    
    # Cleanup test files
    if os.path.exists("reports.json"):
        os.remove("reports.json")
    if os.path.exists("users.json"):
        os.remove("users.json")

if __name__ == "__main__":
    run_tests()