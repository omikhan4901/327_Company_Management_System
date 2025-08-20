# database.py

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, relationship, scoped_session,declarative_base  # IMPORTANT: Added scoped_session
from datetime import datetime
from sqlalchemy import ForeignKey

# Setup the SQLite database
DATABASE_URL = "sqlite:///./company.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# IMPORTANT: SessionLocal must be a scoped_session for .remove() to work in tests
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine)) 
Base = declarative_base()

# Define Database Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True) # Link to Department
    
    # Optional: Define relationship to easily access department object
    department = relationship("Department")
    
class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    assigned_to = Column(String) # Still assigned by username
    deadline = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    type = Column(String) # Ensure 'type' is here if using Factory Method for task types
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    department = relationship("Department")

class Payslip(Base):
    __tablename__ = "payslips"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, index=True)
    base_salary = Column(Float)
    hours_worked = Column(Float)
    overtime_hours = Column(Float)
    salary = Column(Float)
    month = Column(String)
    year = Column(Integer)
    strategy = Column(String)
    generated_at = Column(DateTime, default=datetime.now)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    department = relationship("Department")

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, index=True)
    date = Column(String)
    check_in = Column(String)
    check_out = Column(String, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    department = relationship("Department")

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    parent_department_id = Column(Integer, nullable=True) # For hierarchical structure

# Create the database tables
def create_tables():
    Base.metadata.create_all(bind=engine)
