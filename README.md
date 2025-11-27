# Batch Python Service

A lightweight batch processing service inspired by Spring Batch, built with FastAPI and SQLModel.

## Features

- **Job Management**: Define jobs with multiple steps.
- **Execution Tracking**: Tracks status (STARTING, STARTED, COMPLETED, FAILED) of Jobs and Steps.
- **Persistence**: Uses SQLite (by default) to store Job Instances and Executions.
- **Error Handling**: Captures exceptions and marks executions as FAILED.
- **Restartability**: Rerunning a job with the same parameters creates a new execution for the same Job Instance.

## Setup

1. Install `uv` (if not already installed):
   ```bash
   brew install uv
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

## Running the Service

```bash
uv run main.py
```

The API will be available at `http://localhost:8000`.

## API Usage

### Launch a Job

```bash
curl -X POST "http://localhost:8000/jobs/SampleJob/launch" \
     -H "Content-Type: application/json" \
     -d '{}'
```

### List Executions

```bash
curl "http://localhost:8000/executions"
```

### Get Specific Execution

```bash
curl "http://localhost:8000/executions/1"
```

### Get Execution Steps

```bash
curl "http://localhost:8000/executions/1/steps"
```

### Restart a Failed Job

To restart a failed job, simply launch it again with the same parameters. The system will detect the existing job instance and skip any steps that have already completed successfully.

```bash
curl -X POST "http://localhost:8000/jobs/FailingJob/launch" \
     -H "Content-Type: application/json" \
     -d '{}'
```

### Force Execution

To force a job to run all steps, even if they have previously completed successfully, use the `force=true` query parameter.

```bash
curl -X POST "http://localhost:8000/jobs/SampleJob/launch?force=true" \
     -H "Content-Type: application/json" \
     -d '{}'
```

## Defining New Jobs

Edit `app/jobs.py` to add new jobs.

```python
def my_logic():
    print("Doing work...")

my_job = Job(name="MyJob", steps=[Step(name="Step1", task=my_logic)])
job_registry["MyJob"] = my_job
```
