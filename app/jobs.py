import time
import random
from datetime import datetime
from app.core import Job, Step, ChunkStep
from app.chunk import (
    ListItemReader, 
    FunctionItemProcessor, 
    CallableItemWriter,
    ListItemWriter
)

def step1_logic():
    print("Executing Step 1")
    time.sleep(1)
    print("Step 1 Complete")

def step2_logic():
    print("Executing Step 2")
    time.sleep(1)
    print("Step 2 Complete")

def error_step_logic():
    print("Executing Error Step")
    raise Exception("Something went wrong!")

def flaky_step_logic():
    """A step that randomly fails to demonstrate retry logic."""
    print("Executing Flaky Step")
    if random.random() < 0.7:  # 70% chance of failure
        raise Exception("Transient error occurred!")
    print("Flaky Step succeeded!")

def parameterized_step_logic():
    """A step that would use job parameters (demonstration)."""
    print("Executing Parameterized Step")
    time.sleep(0.5)
    print("Parameterized Step Complete")

# Chunk processing functions
def process_number(num: int) -> int:
    """Example processor: square the number and filter out odd results."""
    result = num * num
    if result % 2 == 0:  # Only keep even squares
        return result
    return None  # Filter out odd squares

# Output storage for demonstration
chunk_output = []

def write_chunk(items):
    """Example writer: print and store the chunk."""
    print(f"Writing chunk of {len(items)} items: {items}")
    chunk_output.extend(items)

sample_job = Job(
    name="SampleJob",
    steps=[
        Step(name="Step1", task=step1_logic),
        Step(name="Step2", task=step2_logic),
    ]
)

failing_job = Job(
    name="FailingJob",
    steps=[
        Step(name="Step1", task=step1_logic),
        Step(name="ErrorStep", task=error_step_logic),
    ]
)

# Job with retry logic
retry_job = Job(
    name="RetryJob",
    steps=[
        Step(name="Step1", task=step1_logic),
        Step(name="FlakyStep", task=flaky_step_logic, max_retries=3, retry_delay=1.0),
        Step(name="Step2", task=step2_logic),
    ]
)

# Job that accepts parameters
parameterized_job = Job(
    name="ParameterizedJob",
    steps=[
        Step(name="ParameterizedStep", task=parameterized_step_logic),
        Step(name="FinalStep", task=step2_logic),
    ]
)

# Chunk processing job
chunk_job = Job(
    name="ChunkJob",
    steps=[
        ChunkStep(
            name="ProcessNumbers",
            reader=ListItemReader(list(range(1, 51))),  # Read numbers 1-50
            processor=FunctionItemProcessor(process_number),  # Square and filter
            writer=CallableItemWriter(write_chunk),  # Write chunks
            chunk_size=10  # Process 10 items at a time
        )
    ]
)

# Registry of available jobs
job_registry = {
    "SampleJob": sample_job,
    "FailingJob": failing_job,
    "RetryJob": retry_job,
    "ParameterizedJob": parameterized_job,
    "ChunkJob": chunk_job,
}
