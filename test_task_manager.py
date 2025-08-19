# test/test_task_manager.py

from task_manager import TaskManager


def run_tests():
    tm = TaskManager(file_path="test_tasks.json")  # use test file to avoid overwriting prod

    print("\n--- Create Base Task ---")
    task_id1 = tm.create_task(
        title="Design system diagram",
        description="Draw and finalize UML sequence diagram",
        assigned_to="mohaimen",
        deadline="2025-08-15"
    )
    print("Created Task ID:", task_id1)

    print("\n--- Create High Priority Task ---")
    task_id2 = tm.create_task(
        title="Fix critical bug",
        description="Resolve production outage issue",
        assigned_to="alice",
        deadline="2025-08-12",
        task_type="HighPriorityTask"
    )
    print("Created Task ID:", task_id2)

    print("\n--- Create Deadline Sensitive Task ---")
    task_id3 = tm.create_task(
        title="Submit project proposal",
        description="Finalize and submit project proposal document",
        assigned_to="bob",
        deadline="2025-08-18",
        task_type="DeadlineSensitiveTask"
    )
    print("Created Task ID:", task_id3)

    print("\n--- Update Status ---")
    result = tm.update_task_status(task_id1, "In Progress")
    print("Update result:", result)

    print("\n--- Get Task by ID ---")
    print(tm.get_task_by_id(task_id1))

    print("\n--- Tasks for mohaimen ---")
    tasks = tm.get_tasks_by_user("mohaimen")
    for task in tasks:
        print(task)

    print("\n--- Tasks for alice ---")
    tasks = tm.get_tasks_by_user("alice")
    for task in tasks:
        print(task)

    print("\n--- All Tasks ---")
    for task in tm.get_all_tasks():
        print(task)


if __name__ == "__main__":
    run_tests()
