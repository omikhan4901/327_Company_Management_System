# test/test_task_manager.py

from task_manager import TaskManager

def run_tests():
    tm = TaskManager()

    print("\n--- Create Task ---")
    task_id = tm.create_task(
        title="Design system diagram",
        description="Draw and finalize UML sequence diagram",
        assigned_to="mohaimen",
        deadline="2025-08-15"
    )
    print("Created Task ID:", task_id)

    print("\n--- Update Status ---")
    result = tm.update_task_status(task_id, "In Progress")
    print("Update result:", result)

    print("\n--- Get Task by ID ---")
    print(tm.get_task_by_id(task_id))

    print("\n--- Tasks for mohaimen ---")
    tasks = tm.get_tasks_by_user("mohaimen")
    for task in tasks:
        print(task)

    print("\n--- All Tasks ---")
    for task in tm.get_all_tasks():
        print(task)

if __name__ == "__main__":
    run_tests()
