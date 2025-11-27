"""
Example: Custom Chunk Processing Components

This example shows how to create custom ItemReaders and ItemWriters
for real-world use cases like reading from files and writing to databases.
"""

from app.chunk import ItemReader, ItemWriter, ItemProcessor
from typing import Optional, List
import csv
import json

# Example 1: CSV File Reader
class CSVFileReader(ItemReader[dict]):
    """Reads items from a CSV file."""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.file = None
        self.reader = None
        self._open_file()
    
    def _open_file(self):
        self.file = open(self.filename, 'r')
        self.reader = csv.DictReader(self.file)
    
    def read(self) -> Optional[dict]:
        try:
            return next(self.reader)
        except StopIteration:
            self.file.close()
            return None
    
    def reset(self):
        """Reset reader to beginning of file."""
        if self.file:
            self.file.close()
        self._open_file()

# Example 2: JSON Lines Reader
class JSONLinesReader(ItemReader[dict]):
    """Reads items from a JSON Lines file (one JSON object per line)."""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.file = None
        self._open_file()
    
    def _open_file(self):
        self.file = open(self.filename, 'r')
    
    def read(self) -> Optional[dict]:
        line = self.file.readline()
        if not line:
            self.file.close()
            return None
        return json.loads(line.strip())
    
    def reset(self):
        if self.file:
            self.file.close()
        self._open_file()

# Example 3: Database Writer (pseudo-code)
class DatabaseWriter(ItemWriter[dict]):
    """Writes items to a database table."""
    
    def __init__(self, table_name: str, connection):
        self.table_name = table_name
        self.connection = connection
    
    def write(self, items: List[dict]) -> None:
        """Bulk insert items into database."""
        if not items:
            return
        
        # Example using SQLAlchemy or similar
        # cursor = self.connection.cursor()
        # cursor.executemany(f"INSERT INTO {self.table_name} VALUES (...)", items)
        # self.connection.commit()
        
        print(f"Writing {len(items)} items to {self.table_name}")

# Example 4: File Writer
class JSONFileWriter(ItemWriter[dict]):
    """Writes items to a JSON file."""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.file = open(filename, 'w')
    
    def write(self, items: List[dict]) -> None:
        for item in items:
            self.file.write(json.dumps(item) + '\n')
        self.file.flush()
    
    def __del__(self):
        if hasattr(self, 'file') and self.file:
            self.file.close()

# Example 5: Data Transformation Processor
class DataCleaningProcessor(ItemProcessor[dict, dict]):
    """Cleans and validates data items."""
    
    def process(self, item: dict) -> Optional[dict]:
        # Filter out invalid items
        if not item.get('id'):
            return None  # Skip items without ID
        
        # Transform data
        cleaned = {
            'id': int(item['id']),
            'name': item.get('name', '').strip().upper(),
            'value': float(item.get('value', 0))
        }
        
        # Filter based on business rules
        if cleaned['value'] < 0:
            return None  # Skip negative values
        
        return cleaned

# Example Usage:
"""
from app.core import Job, ChunkStep

# Create a job that reads from CSV, cleans data, and writes to database
data_migration_job = Job(
    name="DataMigration",
    steps=[
        ChunkStep(
            name="MigrateCustomers",
            reader=CSVFileReader("customers.csv"),
            processor=DataCleaningProcessor(),
            writer=DatabaseWriter("customers", db_connection),
            chunk_size=100  # Process 100 records at a time
        )
    ]
)
"""
