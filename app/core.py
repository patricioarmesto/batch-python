import traceback
from datetime import datetime
from typing import List, Callable, Any
from sqlmodel import Session, select
from app.models import JobInstance, JobExecution, StepExecution, BatchStatus
from app.database import engine

class Step:
    def __init__(self, name: str, task: Callable[..., Any]):
        self.name = name
        self.task = task

class Job:
    def __init__(self, name: str, steps: List[Step]):
        self.name = name
        self.steps = steps

class JobLauncher:
    def __init__(self):
        pass

    def run_job(self, job: Job, parameters: dict = None, force: bool = False):
        if parameters is None:
            parameters = {}
        
        # Simple key generation based on sorted parameters
        job_key = str(sorted(parameters.items()))
        
        with Session(engine) as session:
            # 1. Find or Create JobInstance
            statement = select(JobInstance).where(
                JobInstance.job_name == job.name,
                JobInstance.job_key == job_key
            )
            job_instance = session.exec(statement).first()
            
            if not job_instance:
                job_instance = JobInstance(job_name=job.name, job_key=job_key)
                session.add(job_instance)
                session.commit()
                session.refresh(job_instance)
            
            # Check for already completed steps for this instance
            completed_steps = set()
            if not force:
                statement = select(StepExecution.step_name).join(JobExecution).where(
                    JobExecution.job_instance_id == job_instance.id,
                    StepExecution.status == BatchStatus.COMPLETED
                )
                results = session.exec(statement).all()
                completed_steps.update(results)

            # 2. Create JobExecution
            job_execution = JobExecution(
                job_instance_id=job_instance.id,
                status=BatchStatus.STARTED,
                start_time=datetime.utcnow()
            )
            session.add(job_execution)
            session.commit()
            session.refresh(job_execution)
            
            try:
                for step in job.steps:
                    if step.name in completed_steps:
                        print(f"Skipping step {step.name} as it is already complete.")
                        continue
                    self._run_step(session, job_execution, step)
                
                job_execution.status = BatchStatus.COMPLETED
                job_execution.exit_code = "COMPLETED"
            except Exception as e:
                job_execution.status = BatchStatus.FAILED
                job_execution.exit_code = "FAILED"
                job_execution.exit_message = str(e)
                print(f"Job failed: {e}")
                traceback.print_exc()
            finally:
                job_execution.end_time = datetime.utcnow()
                session.add(job_execution)
                session.commit()
                
            return job_execution

    def _run_step(self, session: Session, job_execution: JobExecution, step: Step):
        step_execution = StepExecution(
            job_execution_id=job_execution.id,
            step_name=step.name,
            status=BatchStatus.STARTED,
            start_time=datetime.utcnow()
        )
        session.add(step_execution)
        session.commit()
        session.refresh(step_execution)
        
        try:
            # Execute the step logic
            step.task()
            
            step_execution.status = BatchStatus.COMPLETED
            step_execution.exit_code = "COMPLETED"
        except Exception as e:
            step_execution.status = BatchStatus.FAILED
            step_execution.exit_code = "FAILED"
            step_execution.exit_message = str(e)
            raise e # Re-raise to stop the job
        finally:
            step_execution.end_time = datetime.utcnow()
            session.add(step_execution)
            session.commit()
