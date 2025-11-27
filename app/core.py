import traceback
import time
from datetime import datetime
from typing import List, Callable, Any, Union
from sqlmodel import Session, select
from app.models import JobInstance, JobExecution, StepExecution, BatchStatus, JobParameter
from app.database import engine

class Step:
    def __init__(self, name: str, task: Callable[..., Any], max_retries: int = 0, retry_delay: float = 1.0):
        self.name = name
        self.task = task
        self.max_retries = max_retries
        self.retry_delay = retry_delay  # seconds


class ChunkStep:
    """A step that processes data in chunks using reader, processor, and writer."""
    
    def __init__(self, name: str, reader, processor=None, writer=None, 
                 chunk_size: int = 10, max_retries: int = 0, retry_delay: float = 1.0,
                 skip_policy=None):
        self.name = name
        self.reader = reader
        self.processor = processor
        self.writer = writer
        self.chunk_size = chunk_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.skip_policy = skip_policy
        self.is_chunk_step = True

class Job:
    def __init__(self, name: str, steps: List[Union[Step, ChunkStep]]):
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
                
                # Save parameters
                self._save_parameters(session, job_instance.id, parameters)
            
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
                    
                    # Check if it's a chunk step or regular step
                    if hasattr(step, 'is_chunk_step') and step.is_chunk_step:
                        self._run_chunk_step(session, job_execution, step)
                    else:
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

    def _save_parameters(self, session: Session, job_instance_id: int, parameters: dict):
        """Save job parameters to the database with type detection."""
        for key, value in parameters.items():
            param = JobParameter(job_instance_id=job_instance_id, key_name=key)
            
            if isinstance(value, str):
                param.string_value = value
            elif isinstance(value, datetime):
                param.date_value = value
            elif isinstance(value, int):
                param.long_value = value
            elif isinstance(value, float):
                param.double_value = value
            else:
                # Default to string representation
                param.string_value = str(value)
            
            session.add(param)
        session.commit()

    def _run_step(self, session: Session, job_execution: JobExecution, step: Step):
        step_execution = StepExecution(
            job_execution_id=job_execution.id,
            step_name=step.name,
            status=BatchStatus.STARTED,
            start_time=datetime.utcnow(),
            retry_count=0
        )
        session.add(step_execution)
        session.commit()
        session.refresh(step_execution)
        
        retry_count = 0
        last_exception = None
        
        while retry_count <= step.max_retries:
            try:
                # Execute the step logic
                step.task()
                
                step_execution.status = BatchStatus.COMPLETED
                step_execution.exit_code = "COMPLETED"
                step_execution.retry_count = retry_count
                step_execution.end_time = datetime.utcnow()
                session.add(step_execution)
                session.commit()
                return  # Success, exit the retry loop
                
            except Exception as e:
                last_exception = e
                retry_count += 1
                
                if retry_count <= step.max_retries:
                    print(f"Step {step.name} failed (attempt {retry_count}/{step.max_retries + 1}). Retrying in {step.retry_delay}s...")
                    time.sleep(step.retry_delay)
                else:
                    # All retries exhausted
                    print(f"Step {step.name} failed after {retry_count} attempts.")
                    step_execution.status = BatchStatus.FAILED
                    step_execution.exit_code = "FAILED"
                    step_execution.exit_message = str(e)
                    step_execution.retry_count = retry_count - 1
                    step_execution.end_time = datetime.utcnow()
                    session.add(step_execution)
                    session.commit()
                    raise e  # Re-raise to stop the job

    def _run_chunk_step(self, session: Session, job_execution: JobExecution, step):
        """Execute a chunk-oriented step with read-process-write cycle."""
        from app.chunk import PassThroughProcessor
        
        step_execution = StepExecution(
            job_execution_id=job_execution.id,
            step_name=step.name,
            status=BatchStatus.STARTED,
            start_time=datetime.utcnow(),
            retry_count=0,
            read_count=0,
            write_count=0,
            filter_count=0,
            commit_count=0
        )
        session.add(step_execution)
        session.commit()
        session.refresh(step_execution)
        
        # Use PassThroughProcessor if no processor specified
        processor = step.processor if step.processor else PassThroughProcessor()
        
        retry_count = 0
        
        while retry_count <= step.max_retries:
            try:
                # Process items in chunks
                while True:
                    chunk = []
                    
                    # Read a chunk
                    for _ in range(step.chunk_size):
                        item = step.reader.read()
                        if item is None:
                            break
                        chunk.append(item)
                        step_execution.read_count += 1
                    
                    if not chunk:
                        break  # No more items to process
                    
                    # Process the chunk
                    processed_chunk = []
                    for item in chunk:
                        processed_item = processor.process(item)
                        if processed_item is not None:
                            processed_chunk.append(processed_item)
                        else:
                            step_execution.filter_count += 1
                    
                    # Write the processed chunk
                    if processed_chunk and step.writer:
                        step.writer.write(processed_chunk)
                        step_execution.write_count += len(processed_chunk)
                    
                    step_execution.commit_count += 1
                    
                    # Commit after each chunk
                    session.add(step_execution)
                    session.commit()
                
                # Step completed successfully
                step_execution.status = BatchStatus.COMPLETED
                step_execution.exit_code = "COMPLETED"
                step_execution.retry_count = retry_count
                step_execution.end_time = datetime.utcnow()
                session.add(step_execution)
                session.commit()
                return
                
            except Exception as e:
                retry_count += 1
                
                if retry_count <= step.max_retries:
                    print(f"Chunk step {step.name} failed (attempt {retry_count}/{step.max_retries + 1}). Retrying in {step.retry_delay}s...")
                    time.sleep(step.retry_delay)
                    # Reset reader if possible
                    if hasattr(step.reader, 'reset'):
                        step.reader.reset()
                else:
                    # All retries exhausted
                    print(f"Chunk step {step.name} failed after {retry_count} attempts.")
                    step_execution.status = BatchStatus.FAILED
                    step_execution.exit_code = "FAILED"
                    step_execution.exit_message = str(e)
                    step_execution.retry_count = retry_count - 1
                    step_execution.end_time = datetime.utcnow()
                    session.add(step_execution)
                    session.commit()
                    raise e
