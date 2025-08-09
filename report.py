import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from threading import Lock
from authentication import AuthManager

class Report(ABC):
    """Abstract base class for reports"""
    def __init__(self, title, creator):
        self.title = title
        self.creator = creator
        self.created_at = datetime.now().isoformat()
        self.data = {}
    
    @abstractmethod
    def generate(self):
        """Generate the report content"""
        pass
    
    @abstractmethod
    def get_report_type(self):
        """Get the type of report"""
        pass
    
    def to_dict(self):
        """Convert report to dictionary"""
        return {
            "title": self.title,
            "type": self.get_report_type(),
            "creator": self.creator,
            "created_at": self.created_at,
            "content": self.generate()
        }

class FullReport(Report):
    """Full detailed report"""
    def __init__(self, title, creator, content):
        super().__init__(title, creator)
        self.data = content
    
    def generate(self):
        """Generate full report with all details"""
        return {
            "metadata": {
                "report_title": self.title,
                "generated_at": self.created_at,
                "generated_by": self.creator
            },
            "content": self.data,
            "summary": f"Full report containing {len(self.data)} data points"
        }
    
    def get_report_type(self):
        return "full"

class PartialReport(Report):
    """Partial summary report"""
    def __init__(self, title, creator, content):
        super().__init__(title, creator)
        self.data = content
    
    def generate(self):
        """Generate partial report with key metrics"""
        return {
            "report_title": self.title,
            "key_metrics": {
                "total_items": len(self.data),
                "first_item": self.data[0] if self.data else None,
                "last_item": self.data[-1] if self.data else None
            }
        }
    
    def get_report_type(self):
        return "partial"

class VisualReport(Report):
    """Report with visual representation"""
    def __init__(self, title, creator, content, chart_type="bar"):
        super().__init__(title, creator)
        self.data = content
        self.chart_type = chart_type
    
    def generate(self):
        """Generate report with visualization data"""
        return {
            "report_title": self.title,
            "chart_type": self.chart_type,
            "datapoints": self.data,
            "stats": {
                "min": min(self.data) if self.data else None,
                "max": max(self.data) if self.data else None,
                "avg": sum(self.data)/len(self.data) if self.data else None
            }
        }
    
    def get_report_type(self):
        return "visual"

class ReportFactory:
    """Factory for creating different types of reports"""
    @staticmethod
    def create_report(report_type, title, creator, content, **kwargs):
        """Create a report based on type"""
        if report_type == "full":
            return FullReport(title, creator, content)
        elif report_type == "partial":
            return PartialReport(title, creator, content)
        elif report_type == "visual":
            return VisualReport(title, creator, content, kwargs.get("chart_type", "bar"))
        else:
            raise ValueError(f"Unknown report type: {report_type}")

class ReportManager:
    """Manages report generation and storage"""
    _instance = None
    _lock = Lock()
    _reports_file = "reports.json"
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ReportManager, cls).__new__(cls)
                cls._instance.reports = {}
                cls._instance._load_reports_from_file()
        return cls._instance
    
    def _load_reports_from_file(self):
        """Load reports from JSON file"""
        if os.path.exists(self._reports_file):
            with open(self._reports_file, "r") as f:
                try:
                    self.reports = json.load(f)
                    print(f"[INFO] Loaded {len(self.reports)} reports from {self._reports_file}")
                except json.JSONDecodeError:
                    print("[ERROR] Failed to decode reports file. Starting with empty report list.")
        else:
            print("[INFO] No reports file found. Starting fresh.")
    
    def _save_reports_to_file(self):
        """Save reports to JSON file"""
        with open(self._reports_file, "w") as f:
            json.dump(self.reports, f, indent=4)
        print(f"[INFO] Saved {len(self.reports)} reports to {self._reports_file}")
    
    def generate_report(self, token, report_type, title, content, **kwargs):
        """Generate and store a new report"""
        auth = AuthManager()
        if not auth.validate_token(token):
            return False, "Invalid authentication token"
        
        creator = auth.get_logged_in_user(token)
        if not creator:
            return False, "User not found"
        
        try:
            report = ReportFactory.create_report(
                report_type=report_type,
                title=title,
                creator=creator,
                content=content,
                **kwargs
            )
            
            report_id = str(len(self.reports) + 1)
            self.reports[report_id] = report.to_dict()
            self._save_reports_to_file()
            
            return True, {"report_id": report_id, "report": report.generate()}
        except ValueError as e:
            return False, str(e)
    
    def get_report(self, token, report_id):
        """Retrieve a generated report"""
        auth = AuthManager()
        if not auth.validate_token(token):
            return False, "Invalid authentication token"
        
        if report_id not in self.reports:
            return False, "Report not found"
        
        return True, self.reports[report_id]
    
    def list_reports(self, token):
        """List all available reports"""
        auth = AuthManager()
        if not auth.validate_token(token):
            return False, "Invalid authentication token"
        
        # Return simplified list of reports
        simplified = {
            report_id: {
                "title": report["title"],
                "type": report["type"],
                "creator": report["creator"],
                "created_at": report["created_at"]
            }
            for report_id, report in self.reports.items()
        }
        return True, simplified