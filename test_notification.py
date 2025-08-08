# test/test_notification.py

from notification import NotificationManager, InAppNotifier, EmailNotifier

def run_tests():
    notify = NotificationManager()

    # Create channels
    in_app = InAppNotifier()
    email = EmailNotifier()

    # Register observers
    notify.add_notifier(in_app)
    notify.add_notifier(email)

    # Send a few sample messages
    notify.send_notification("Task 'Payroll Summary' assigned to you.", "john")
    notify.send_notification("Your payslip for August is generated.", "mohaimen")

    print("\n--- Stored In-App Notifications ---")
    for note in in_app.notifications:
        print(note)

if __name__ == "__main__":
    run_tests()
