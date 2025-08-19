# test/test_facade.py

from report_facade import ReportFacade


def run_facade_tests():
    facade = ReportFacade()

    print("\n--- [Employee Summary: john] ---")
    john_summary = facade.get_employee_summary("john")
    for key, val in john_summary.items():
        print(f"{key}: {val}")

    print("\n--- [System Summary] ---")
    system_summary = facade.get_system_summary()
    for key, val in system_summary.items():
        print(f"{key}: {val}")


if __name__ == "__main__":
    run_facade_tests()

