# test/test_notification.py

from notification import NotificationManager, InAppNotifier, EmailNotifier

def run_tests():
    manager = NotificationManager()

    # Observers auto-register with subject
    in_app = InAppNotifier(manager.subject)
    email = EmailNotifier(manager.subject)

    # Send a few sample messages
    manager.send_notification("Task 'Payroll Summary' assigned to you.", "john")
    manager.send_notification("Your payslip for August is generated.", "mohaimen")

    print("\n--- Stored In-App Notifications ---")
    for note in in_app.notifications:
        print(note)

if __name__ == "__main__":
    run_tests()
