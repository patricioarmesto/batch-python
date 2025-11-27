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

## Advanced Features

### Retry Logic

Steps can be configured with automatic retry on failure:

```python
Step(
    name="FlakyStep", 
    task=flaky_task, 
    max_retries=3,      # Retry up to 3 times
    retry_delay=1.0     # Wait 1 second between retries
)
```

Example job with retry:
```bash
curl -X POST "http://localhost:8000/jobs/RetryJob/launch" \
     -H "Content-Type: application/json" \
     -d '{}'
```

### Job Parameters

Jobs can accept typed parameters that are stored with the job instance:

```bash
curl -X POST "http://localhost:8000/jobs/ParameterizedJob/launch" \
     -H "Content-Type: application/json" \
     -d '{"start_date": "2024-01-01", "batch_size": 100, "threshold": 0.95}'
```

Supported parameter types:
- **String**: Text values
- **Integer**: Whole numbers
- **Float**: Decimal numbers
- **DateTime**: ISO format dates (automatically detected)

View parameters for a job instance:
```bash
curl "http://localhost:8000/instances/1/parameters"
```

### Chunk Processing

Process large datasets efficiently using the **read-process-write** pattern with automatic chunking and transaction management.

**Key Concepts:**
- **ItemReader**: Reads items one at a time from a data source
- **ItemProcessor**: Transforms items (can filter by returning `None`)
- **ItemWriter**: Writes chunks of processed items
- **Chunk Size**: Number of items to process before committing

**Example:**

```python
from app.core import ChunkStep
from app.chunk import ListItemReader, FunctionItemProcessor, CallableItemWriter

def process_item(item):
    # Transform the item
    return item * 2

def write_items(items):
    # Write the chunk
    print(f"Writing {len(items)} items")

chunk_step = ChunkStep(
    name="ProcessData",
    reader=ListItemReader([1, 2, 3, 4, 5]),
    processor=FunctionItemProcessor(process_item),
    writer=CallableItemWriter(write_items),
    chunk_size=10  # Commit every 10 items
)
```

**Built-in Components:**
- `ListItemReader`: Read from a Python list
- `CallableItemReader`: Read from any iterator/generator
- `FunctionItemProcessor`: Process using a function
- `PassThroughProcessor`: No transformation (identity)
- `ListItemWriter`: Write to a Python list
- `CallableItemWriter`: Write using a custom function

**Metrics Tracked:**
- `read_count`: Total items read
- `write_count`: Total items written
- `filter_count`: Items filtered out by processor
- `commit_count`: Number of chunk commits

Test the chunk job:
```bash
curl -X POST "http://localhost:8000/jobs/ChunkJob/launch" \
     -H "Content-Type: application/json" \
     -d '{}'
```

View chunk metrics:
```bash
curl "http://localhost:8000/executions/1/steps"
```

### Available Sample Jobs

- **SampleJob**: Basic two-step job
- **FailingJob**: Demonstrates error handling
- **RetryJob**: Demonstrates automatic retry logic with a flaky step
- **ParameterizedJob**: Demonstrates job parameters
- **ChunkJob**: Demonstrates chunk-oriented processing (reads 50 numbers, squares them, filters, writes in chunks of 10)
