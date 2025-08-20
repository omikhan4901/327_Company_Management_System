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
        source ./venv/Scripts/activate
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

# Design Patterns Used 📐

## **1. Adapter Pattern**

**Definition:**
The **Adapter pattern** allows the interface of an existing class to be used as another interface. It’s like a translator between two incompatible interfaces.

**Basic Example:**

```python
class OldPrinter:
    def print_text(self, text): 
        return f"Old printing: {text}"

class PrinterAdapter:
    def __init__(self, old_printer):
        self.old_printer = old_printer
    def print(self, text):  # New interface
        return self.old_printer.print_text(text)

printer = PrinterAdapter(OldPrinter())
print(printer.print("Hello!"))  # Output: "Old printing: Hello!"
```

**Our System Example:**

* **Adapter Classes:** `AttendanceAdapter`, `AttendanceManagerAdapter`
* **Purpose:** Converts Our database attendance objects to a standard Python object with methods like `get_hours_worked()` for Our business logic.

```python
attendance_adapter = AttendanceAdapter(db_entry)
hours = attendance_adapter.get_hours_worked()
```

---

## **2. Composite Pattern**

**Definition:**
The **Composite pattern** allows you to treat individual objects and compositions of objects uniformly. Perfect for hierarchical structures.

**Basic Example:**

```python
class Component:
    def operation(self): pass

class Leaf(Component):
    def operation(self): return "Leaf"

class Composite(Component):
    def __init__(self):
        self.children = []
    def add(self, child): self.children.append(child)
    def operation(self):
        return " + ".join(child.operation() for child in self.children)

tree = Composite()
tree.add(Leaf())
tree.add(Leaf())
print(tree.operation())  # Output: "Leaf + Leaf"
```

**Our System Example:**

* **Composite Classes:** `DepartmentComposite`, `DepartmentLeaf`
* **Purpose:** Manage hierarchy of departments and employees, treating a single employee and a whole department uniformly.

```python
company = DepartmentComposite("Company")
dept1 = DepartmentComposite("HR")
emp1 = DepartmentLeaf("Alice")
dept1.add(emp1)
company.add(dept1)
```

---

## **3. Strategy Pattern**

**Definition:**
The **Strategy pattern** defines a family of algorithms, encapsulates each one, and makes them interchangeable.

**Basic Example:**

```python
class Strategy:
    def execute(self, data): pass

class ConcreteStrategyA(Strategy):
    def execute(self, data): return data * 2

class Context:
    def __init__(self, strategy): self.strategy = strategy
    def run(self, data): return self.strategy.execute(data)

context = Context(ConcreteStrategyA())
print(context.run(5))  # Output: 10
```

**Our System Example:**

* **Strategy Classes:** `ConcreteStrategyA`, `ConcreteStrategyB`
* **Context:** `PayrollManager`
* **Purpose:** Choose how salary is calculated (standard hourly vs. commission) at runtime.

```python
payroll = PayrollManager()
payroll.set_strategy(ConcreteStrategyB())
salary = payroll.generate_payslip(employee_id, ...)
```

---

## **4. Observer Pattern**

**Definition:**
The **Observer pattern** defines a one-to-many dependency so that when one object changes state, all its dependents are notified automatically.

**Basic Example:**

```python
class Subject:
    def __init__(self): self.observers = []
    def attach(self, obs): self.observers.append(obs)
    def notify(self, msg): 
        for obs in self.observers: obs.update(msg)

class Observer:
    def update(self, msg): print(f"Observer received: {msg}")

subject = Subject()
subject.attach(Observer())
subject.notify("Hello!")  # Output: "Observer received: Hello!"
```

**Our System Example:**

* **Subject:** `NotificationSubject`
* **Observers:** `InAppNotifier`, `EmailNotifier`
* **Manager:** `NotificationManager`
* **Purpose:** Notify employees automatically whenever a task is assigned or a payslip is generated.

```python
notifier = InAppNotifier(NotificationSubject())
notifier.send_notification("Task assigned", "emp123")
```

---

## **5. Factory Method Pattern**

**Definition:**
The **Factory Method pattern** defines an interface for creating an object but lets subclasses decide which class to instantiate.

**Basic Example:**

```python
class Creator:
    def factory_method(self): pass
    def create(self): return self.factory_method()

class ConcreteCreatorA(Creator):
    def factory_method(self): return "ProductA"

creator = ConcreteCreatorA()
print(creator.create())  # Output: "ProductA"
```

**Our System Example:**

* **Creator Classes:** `TaskCreator` and subclasses (`BaseTaskCreator`, `HighPriorityTaskCreator`, `DeadlineSensitiveTaskCreator`)
* **Products:** `TaskModel` and its subclasses
* **Manager:** `TaskManager`
* **Purpose:** Dynamically create different types of tasks without changing the client code.

```python
creator = TaskCreator.get_creator("HighPriorityTask")
task = creator.create_task("Title", "Desc", "emp123", "2025-08-31")
```

---

## **6. Facade Pattern**

**Definition:**
The **Facade pattern** provides a simplified interface to a complex subsystem.

**Basic Example:**

```python
class SubsystemA: 
    def op1(self): return "A1"
class SubsystemB: 
    def op2(self): return "B2"

class Facade:
    def __init__(self): self.a = SubsystemA(); self.b = SubsystemB()
    def simple_op(self): return f"{self.a.op1()} + {self.b.op2()}"

facade = Facade()
print(facade.simple_op())  # Output: "A1 + B2"
```

**Our System Example:**

* **Subsystems:** `TaskReport`, `PayslipReport`, `HoursReport`, `PayReport`, `SystemReport`
* **Facade:** `ReportFacade`
* **Purpose:** Provide a single entry point to generate employee and system reports.

```python
facade = ReportFacade()
emp_summary = facade.get_employee_summary("emp123")
system_summary = facade.get_system_summary()
```

---

✅ **Summary Table**

| Pattern        | Purpose                         | Our Classes                                                                                           |
| -------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Adapter        | Convert incompatible interfaces | `AttendanceAdapter`, `AttendanceManagerAdapter`                                                        |
| Composite      | Hierarchical part-whole         | `DepartmentComposite`, `DepartmentLeaf`                                                                |
| Strategy       | Interchangeable algorithms      | `ConcreteStrategyA/B`, `PayrollManager`                                                                |
| Observer       | Automatic notifications         | `NotificationSubject`, `NotificationObserver`, `InAppNotifier`, `EmailNotifier`, `NotificationManager` |
| Factory Method | Encapsulate object creation     | `TaskCreator` subclasses, `TaskModel` subclasses, `TaskManager`                                        |
| Facade         | Simplify subsystem access       | `ReportFacade`, `TaskReport`, `PayslipReport`, `HoursReport`, `PayReport`, `SystemReport`              |

---
 
