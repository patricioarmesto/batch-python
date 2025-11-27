from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum

class BatchStatus(str, Enum):
    STARTING = "STARTING"
    STARTED = "STARTED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"

class JobInstance(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_name: str = Field(index=True)
    job_key: str = Field(index=True) # Unique identifier for the job instance (e.g. parameters hash)
    
    executions: List["JobExecution"] = Relationship(back_populates="job_instance")

class JobExecution(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_instance_id: int = Field(foreign_key="jobinstance.id")
    status: BatchStatus = Field(default=BatchStatus.STARTING)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    exit_code: str = Field(default="UNKNOWN")
    exit_message: Optional[str] = None
    
    job_instance: JobInstance = Relationship(back_populates="executions")
    step_executions: List["StepExecution"] = Relationship(back_populates="job_execution")

class StepExecution(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_execution_id: int = Field(foreign_key="jobexecution.id")
    step_name: str
    status: BatchStatus = Field(default=BatchStatus.STARTING)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    exit_code: str = Field(default="UNKNOWN")
    exit_message: Optional[str] = None
    
    job_execution: JobExecution = Relationship(back_populates="step_executions")
