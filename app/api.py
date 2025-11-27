from fastapi import FastAPI, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from typing import List, Dict, Any

from app.database import create_db_and_tables, engine
from app.models import JobInstance, JobExecution, StepExecution
from app.core import JobLauncher
from app.jobs import job_registry

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/jobs/{job_name}/launch")
def launch_job(job_name: str, parameters: Dict[str, Any] = None, force: bool = False, background_tasks: BackgroundTasks = None):
    if job_name not in job_registry:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_registry[job_name]
    launcher = JobLauncher()
    
    # Run in background
    background_tasks.add_task(launcher.run_job, job, parameters, force)
    
    return {"message": "Job submitted", "job_name": job_name}

@app.get("/executions")
def list_executions():
    with Session(engine) as session:
        executions = session.exec(select(JobExecution)).all()
        return executions

@app.get("/executions/{execution_id}")
def get_execution(execution_id: int):
    with Session(engine) as session:
        execution = session.get(JobExecution, execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        return execution

@app.get("/executions/{execution_id}/steps")
def list_execution_steps(execution_id: int):
    with Session(engine) as session:
        steps = session.exec(select(StepExecution).where(StepExecution.job_execution_id == execution_id)).all()
        return steps
