# department_composite.py

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class DepartmentComponent(ABC):
    """
    Abstract base class for Department components.
    Defines the common interface for both individual departments (Leaf)
    and departments with sub-departments (Composite).
    """
    def __init__(self, dept_id: int, name: str, parent_id: Optional[int]):
        self.id = dept_id
        self.name = name
        self.parent_department_id = parent_id

    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Returns basic information about the department component."""
        pass

    @abstractmethod
    def get_all_descendant_ids(self) -> List[int]:
        """
        Recursively gets all IDs of child and grandchild departments.
        Does NOT include the current component's ID.
        """
        pass

class DepartmentLeaf(DepartmentComponent):
    """
    Represents a single department that does not contain any sub-departments.
    It's a "leaf" in the Composite tree structure.
    """
    def __init__(self, dept_id: int, name: str, parent_id: Optional[int]):
        super().__init__(dept_id, name, parent_id)
    
    def get_info(self) -> Dict[str, Any]:
        """Returns information for a leaf department."""
        return {
            "id": self.id,
            "name": self.name,
            "parent_department_id": self.parent_department_id,
            "type": "leaf" # Indicates it's a leaf node
        }

    def get_all_descendant_ids(self) -> List[int]:
        """Leaves have no descendants."""
        return []

class DepartmentComposite(DepartmentComponent):
    """
    Represents a department that can contain other DepartmentComponents (both
    leaves and other composites). It's a "composite" node in the tree structure.
    """
    def __init__(self, dept_id: int, name: str, parent_id: Optional[int]):
        super().__init__(dept_id, name, parent_id)
        self._children: List[DepartmentComponent] = []

    def add(self, component: DepartmentComponent) -> None:
        """Adds a child component to this composite."""
        self._children.append(component)

    def remove(self, component: DepartmentComponent) -> None:
        """Removes a child component from this composite."""
        self._children.remove(component)
    
    def get_info(self) -> Dict[str, Any]:
        """
        Returns information for a composite department, including details
        of its children.
        """
        return {
            "id": self.id,
            "name": self.name,
            "parent_department_id": self.parent_department_id,
            "type": "composite", # Indicates it's a composite node
            "children": [child.get_info() for child in self._children] # Recursively get children's info
        }

    def get_all_descendant_ids(self) -> List[int]:
        """
        Recursively gets all IDs of children and their descendants.
        """
        ids = []
        for child in self._children:
            ids.append(child.id) # Add child's own ID
            ids.extend(child.get_all_descendant_ids()) # Add child's descendants
        return ids