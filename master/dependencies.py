from .services.data_manager import DataManager
from .services.job_manager import JobManager
from .services.local_executor import LocalExecutor
from .services.worker_manager import WorkerManager
from .services.workflow_analyzer import WorkflowAnalyzer

# 전역 인스턴스
data_manager = DataManager()
worker_manager = WorkerManager()
workflow_analyzer = WorkflowAnalyzer()
job_manager = JobManager(data_manager)
local_executor = LocalExecutor() # workflows dir assumed relative

def get_data_manager() -> DataManager:
    return data_manager

def get_job_manager() -> JobManager:
    return job_manager

def get_local_executor() -> LocalExecutor:
    return local_executor

def get_worker_manager() -> WorkerManager:
    return worker_manager

def get_workflow_analyzer() -> WorkflowAnalyzer:
    return workflow_analyzer
