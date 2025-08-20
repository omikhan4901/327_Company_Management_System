## Group Members

| Name | ID / Code |
|---|---|
| Mehboob Ehsan Khan | 2221016642 |
| Mohaimen Al Mamun | 2221726642 |
| Sanjida Jaman | 2212231042 |
| Susmit Talukder | 2221865042 |

---

## How to Use This Project 🚀

This guide will help you set up and run the Company Management System on your local machine.

### Prerequisites

* **Python 3.8+**: Ensure Python is installed on your system.
* **Git**: (Optional, but recommended for cloning)

### Setup Instructions

1.  **Clone the Repository (or Download the Project Files)**:
    If you have Git, use:
    
    - git clone [[Repository_URL]](https://github.com/omikhan4901/327_Company_Management_System.git)
    - cd 327_Company_Management_System
    
    Otherwise, download all project files and navigate to the root directory of the project in your terminal.

2.  **Create a Virtual Environment**:
    It's highly recommended to use a virtual environment to manage project dependencies.
    ```bash
    python -m venv venv
    ```

3.  **Activate the Virtual Environment**:
    * **On Windows**:
        ```bash
        .\\venv\\Scripts\\activate
        ```
    * **On macOS/Linux**:
        ```bash
        source venv/bin/activate
        ```
    Your terminal prompt should change to `(venv)` to indicate the virtual environment is active.

4.  **Install Dependencies**:
    Install all required Python packages using `pip` and the `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the Application**:
    Start the FastAPI application using Uvicorn:
    ```bash
    uvicorn main:app --reload
    ```
    The `--reload` flag enables automatic server restarts when code changes are detected.

6.  **Access the Application**:
    Open your web browser and navigate to the address provided in your terminal (usually `http://127.0.0.1:8000`).

### Initial Login

Upon first run, the system will automatically create a default **Admin** user and an **"Unassigned"** department in the `company.db` SQLite database.

* **Username**: `admin`
* **Password**: `admin`

You can log in with these credentials to access the Admin dashboard and begin setting up departments and managing users.

### Running Tests

To run the automated tests for the project (requires `pytest` installed, which is in `requirements.txt`):

1.  **Ensure Uvicorn is NOT running.**
2.  **Delete the `company.db` file** from your project's root directory. This ensures a clean database for each test run.
3.  **Activate your virtual environment** (if not already active).
4.  **Run pytest**:
    ```bash
    pytest -s
    ```
    The `-s` flag displays `print()` statements from the tests, providing detailed output.

---

## Project Overview 🏢

The **Company Management System** is a robust, modular web-based platform designed to automate, integrate, and enhance the day-to-day operations of a company. It provides centralized control and seamless interaction between departments, managers, and employees.

### Core Functionalities:

* **User Authentication & Authorization**:
    * Secure login and logout.
    * **Role-Based Access Control (RBAC)**: Supports Admin, Manager, and Employee roles with differentiated access to features and data.
    * New user registration defaults to the "Employee" role.
    * Admins can manage user roles (promote/demote) and assign users to specific departments.
    * Admins cannot change the role of another Admin.

* **Department & Hierarchy Management**:
    * Admins can create, update, and delete departments, including nested sub-departments.
    * Supports a hierarchical organizational structure.
    * A default "Unassigned" department is created for new employees.

* **Task Management**:
    * Admins and Managers can create and assign tasks to employees.
    * Employees can view their assigned tasks and update their task status (Not Started, In Progress, Completed).
    * Managers can view tasks for all employees within their assigned department and its sub-departments.

* **Attendance Tracking**:
    * Employees can check in and check out daily.
    * The system records check-in/out times and calculates hours worked.
    * Admins can view all attendance records.
    * Managers can view attendance records for employees within their assigned department and its sub-departments.

* **Payroll Management**:
    * Admins can generate payslips for any employee based on various calculation strategies (e.g., standard hourly, sales commission).
    * Employees can view their own payslips.
    * Managers can view payslips for employees within their assigned department and its sub-departments.
    * Managers cannot generate payslips.

* **Notification System**:
    * Provides in-app notifications for system events (e.g., task assignment, payslip generation).
    * Simulates email notifications for events.

* **Reporting & Analytics**:
    * Admins can view comprehensive system summaries (task status, total hours/pay by employee).
    * Managers can view reports filtered to their assigned department and its sub-departments.
    * Reports (e.g., Task Reports, Payslips) can be downloaded as PDF files.

* **Audit Logging**:
    * Records significant user actions and system events (e.g., login, logout, role changes, task creation, payslip generation) for accountability and debugging.
    * Admins can view a detailed audit log.

---

## Design Patterns Used 📐

This project extensively utilizes nine key design patterns to ensure a robust, scalable, and maintainable codebase.

### 1. **Singleton Pattern** 🌟
* **Concept**: Ensures that a class has only one instance and provides a global point of access to it.
* **How it's followed**: The `AuthManager` (`authentication.py`) and `Logger` (`logger.py`) classes both use a private class variable (`__instance`) and a static method (`get_instance()`) to guarantee that only a single instance is ever created.
* **Benefit**: Centralized control for critical functionalities like user sessions and system-wide logging, preventing conflicts and ensuring consistency.

### 2. **Factory Method Pattern** 🏭
* **Concept**: Defines an interface for creating an object, but lets subclasses decide which class to instantiate.
* **How it's followed**: The `TaskCreator` in `task_manager.py` is the abstract factory that defines `factory_method`. Concrete creators like `BaseTaskCreator` and `HighPriorityTaskCreator` implement this method to return specific task objects (`TaskModel`, `HighPriorityTask`), based on the `task_type` requested.
* **Benefit**: Decouples the client code from the concrete classes being instantiated, allowing for easy introduction of new task types without modifying core task management logic.

### 3. **Strategy Pattern** 🧩
* **Concept**: Defines a family of algorithms, encapsulates each one, and makes them interchangeable.
* **How it's followed**: The `PayrollManager` (`payroll.py`) is the context that uses different `Strategy` implementations (`ConcreteStrategyA` for hourly pay, `ConcreteStrategyB` for sales commission). The payroll calculation method can be changed at runtime by setting a different strategy object.
* **Benefit**: Allows the payroll calculation algorithm to be changed dynamically, making the system flexible for new compensation models without altering the `PayrollManager`'s code.

### 4. **Observer Pattern** 🔔
* **Concept**: Defines a one-to-many dependency so that when one object changes state, all its dependents are notified.
* **How it's followed**: The `NotificationManager` (`notification.py`) is the subject, and `InAppNotifier` and `EmailNotifier` are the observers. The `NotificationManager`'s `notify_all` method automatically calls the `update` method on all registered observers, decoupling event senders from their receivers.
* **Benefit**: Promotes modularity. New notification channels can be added by simply creating a new observer class and registering it with the subject, without changing the core business logic.

### 5. **Facade Pattern** 🏛️
* **Concept**: Provides a simplified interface to a complex subsystem.
* **How it's followed**: The `ReportFacade` (`report_facade.py`) offers a simple interface like `get_employee_summary` and `get_system_summary`. It orchestrates calls to multiple subsystems (`TaskReport`, `PayslipReport`, etc.) to produce a single, comprehensive report, hiding the underlying complexity from the client.
* **Benefit**: Simplifies the client-side interaction with a complex subsystem, reducing dependencies.

### 6. **Adapter Pattern** 🔌
* **Concept**: Converts the interface of a class into another interface clients expect.
* **How it's followed**: The `AttendanceManagerAdapter` (`attendance.py`) allows the `AttendanceManager` to conform to the `AttendanceAdapter` interface. This lets other parts of the system use the `AttendanceManager`'s functionality through a standardized interface.
* **Benefit**: Enables classes with incompatible interfaces to work together, promoting reusability and flexibility.

### 7. **Repository Pattern** 📦
* **Concept**: Abstracts the data layer, providing a collection-like interface for accessing domain objects.
* **How it's followed**: All your manager classes (`AuthManager`, `TaskManager`, etc.) act as repositories. They expose methods like `get_all_users` or `create_task` which encapsulate the details of database queries and data storage, hiding them from the application logic.
* **Benefit**: Decouples business logic from data access logic. This makes the code cleaner and allows for easier migration to different database systems.

### 8. **Data Mapper Pattern** 🗺️
* **Concept**: A layer of mappers that moves data between objects and a database.
* **How it's followed**: Your SQLAlchemy models in `database.py` (`User`, `Task`, `Payslip`, etc.) are your data mappers. They map your Python domain objects to the database tables, making the Python objects unaware of how they are being stored.
* **Benefit**: Ensures that your domain objects are "persistence-ignorant," promoting a clean separation of concerns and makes your domain model more reusable and testable.

### 9. **Composite Design Pattern** 🌳
* **Concept**: Composes objects into tree structures to represent part-whole hierarchies.
* **How it's followed**: The `DepartmentManager` uses `DepartmentComponent`, `DepartmentLeaf`, and `DepartmentComposite` from `department_composite.py` to build a hierarchical tree of departments. This allows operations like filtering tasks for a manager's department and all its sub-departments to be handled uniformly.
* **Benefit**: Simplifies operations on tree-like structures. You can perform actions on a single department or an entire branch of the department tree using the same interface.
