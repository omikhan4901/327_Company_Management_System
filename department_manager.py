# department_manager.py

from database import SessionLocal, Department
from department_composite import ( # Import the Composite components
    DepartmentComponent,
    DepartmentLeaf,
    DepartmentComposite,
)
from typing import Any, Tuple, List, Optional
from collections import defaultdict # Needed for building the tree

class DepartmentManager:
    def __init__(self):
        # We'll build the composite structure on demand or on startup
        pass

    def _build_department_tree(self) -> List[DepartmentComponent]:
        """
        Builds the hierarchical structure of departments from flat database records
        into Composite pattern components.
        """
        db = SessionLocal()
        try:
            departments_db = db.query(Department).all()
            
            # Create component objects for all departments
            # Determine if a department is a composite or a leaf based on whether it has children
            components = {}
            for d in departments_db:
                has_children = any(child.parent_department_id == d.id for child in departments_db)
                if has_children:
                    components[d.id] = DepartmentComposite(d.id, d.name, d.parent_department_id)
                else:
                    components[d.id] = DepartmentLeaf(d.id, d.name, d.parent_department_id)

            # Link children to their parents
            root_departments = []
            for d_db in departments_db:
                component = components[d_db.id]
                if d_db.parent_department_id is None:
                    root_departments.append(component)
                else:
                    parent_component = components.get(d_db.parent_department_id)
                    if isinstance(parent_component, DepartmentComposite):
                        parent_component.add(component)
                    # Handle orphaned children if parent_component is None (optional: log or fix data)
            return root_departments
        finally:
            db.close()

    def create_default_department(self):
        db = SessionLocal()
        try:
            default_dept = db.query(Department).filter(Department.name == "Unassigned").first()
            if not default_dept:
                new_dept = Department(name="Unassigned", parent_department_id=None)
                db.add(new_dept)
                db.commit()
                print("Default department 'Unassigned' created.")
        finally:
            db.close()

    # --- Database-level CRUD operations (used by the manager itself or commands if you re-add them) ---
    def create_department_db(self, name, parent_department_id=None) -> Tuple[bool, Any]:
        db = SessionLocal()
        try:
            if db.query(Department).filter(Department.name == name).first():
                return False, "Department with this name already exists."
            
            # Check for circular dependency if parent_department_id is not None
            if parent_department_id:
                parent_dept = db.query(Department).filter(Department.id == parent_department_id).first()
                if not parent_dept:
                    return False, "Parent department not found."
                
                # Prevent a department from being its own parent or a descendant of itself
                # This is a basic check; a full check would involve traversing the tree
                if parent_department_id == parent_dept.id: # Should not happen with current logic, but good for safety
                    return False, "Cannot set department as its own parent."

            new_department = Department(name=name, parent_department_id=parent_department_id)
            db.add(new_department)
            db.commit()
            db.refresh(new_department)
            return True, new_department
        finally:
            db.close()

    def get_department_by_id_db(self, department_id):
        db = SessionLocal()
        try:
            return db.query(Department).filter(Department.id == department_id).first()
        finally:
            db.close()

    def get_all_departments_db(self) -> List[Department]:
        db = SessionLocal()
        try:
            return db.query(Department).all()
        finally:
            db.close()

    def update_department_db(self, department_id, new_name=None, new_parent_id=None) -> Tuple[bool, Any]:
        db = SessionLocal()
        try:
            department = db.query(Department).filter(Department.id == department_id).first()
            if not department:
                return False, "Department not found."
            
            # Prevent a department from being its own parent
            if new_parent_id == department_id:
                return False, "A department cannot be its own parent."

            # Prevent circular dependencies (more complex check required for full tree traversal)
            if new_parent_id is not None:
                current_dept_id = new_parent_id
                while current_dept_id is not None:
                    if current_dept_id == department_id:
                        return False, "Circular dependency detected: cannot set parent as a descendant."
                    parent_dept = db.query(Department).filter(Department.id == current_dept_id).first()
                    current_dept_id = parent_dept.parent_department_id if parent_dept else None

            if new_name:
                department.name = new_name
            # Only update parent_department_id if explicitly provided (0 means None)
            if new_parent_id is not None:
                department.parent_department_id = new_parent_id if new_parent_id != 0 else None
            
            db.commit()
            return True, "Department updated successfully."
        finally:
            db.close()

    def delete_department_db(self, department_id) -> Tuple[bool, Any]:
        db = SessionLocal()
        try:
            department = db.query(Department).filter(Department.id == department_id).first()
            if not department:
                return False, "Department not found."
            
            # Check for sub-departments
            if db.query(Department).filter(Department.parent_department_id == department_id).first():
                return False, "Cannot delete department with sub-departments. Please reassign them first."
            
            # Check for assigned users (important!)
            from database import User # Import User model here to avoid circular dependency
            if db.query(User).filter(User.department_id == department_id).first():
                return False, "Cannot delete department with assigned users. Please reassign them first."

            db.delete(department)
            db.commit()
            return True, "Department deleted successfully."
        finally:
            db.close()
    
    # --- Public methods for the application using the Composite structure ---
    def get_department_tree(self) -> List[dict]:
        """Returns the department hierarchy as a list of dictionaries (for UI)."""
        root_components = self._build_department_tree()
        return [comp.get_info() for comp in root_components]

    def get_all_department_ids_in_hierarchy(self, root_department_id: int) -> List[int]:
        """
        Returns all department IDs within a given department's hierarchy (including itself).
        This is useful for filtering tasks/attendance for a manager's department.
        """
        db = SessionLocal()
        try:
            # Rebuild a specific branch of the tree to get descendants
            all_depts_flat = db.query(Department).all()
            
            # Find the root department from the flat list
            root_db_dept = next((d for d in all_depts_flat if d.id == root_department_id), None)
            if not root_db_dept:
                return [] # Department not found

            # Create the root component for this specific query
            root_component: DepartmentComponent
            if any(child.parent_department_id == root_db_dept.id for child in all_depts_flat):
                root_component = DepartmentComposite(root_db_dept.id, root_db_dept.name, root_db_dept.parent_department_id)
            else:
                root_component = DepartmentLeaf(root_db_dept.id, root_db_dept.name, root_db_dept.parent_department_id)

            # Recursively add children to this specific root_component
            # This is a simplified tree builder for getting descendant IDs
            queue = [(root_component, root_db_dept)]
            while queue:
                current_comp, current_db_dept = queue.pop(0)
                if isinstance(current_comp, DepartmentComposite):
                    for child_db in all_depts_flat:
                        if child_db.parent_department_id == current_db_dept.id:
                            child_comp: DepartmentComponent
                            if any(grandchild.parent_department_id == child_db.id for grandchild in all_depts_flat):
                                child_comp = DepartmentComposite(child_db.id, child_db.name, child_db.parent_department_id)
                            else:
                                child_comp = DepartmentLeaf(child_db.id, child_db.name, child_db.parent_department_id)
                            current_comp.add(child_comp)
                            queue.append((child_comp, child_db))

            # Get all IDs from the component (including itself)
            all_ids = [root_component.id]
            all_ids.extend(root_component.get_all_descendant_ids())
            return all_ids
        finally:
            db.close()