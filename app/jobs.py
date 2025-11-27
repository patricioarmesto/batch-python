import time
from app.core import Job, Step

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

# Registry of available jobs
job_registry = {
    "SampleJob": sample_job,
    "FailingJob": failing_job,
}
