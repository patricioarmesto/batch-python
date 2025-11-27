from typing import TypeVar, Generic, List, Optional, Callable, Any, Iterator
from abc import ABC, abstractmethod

T = TypeVar('T')
U = TypeVar('U')

class ItemReader(ABC, Generic[T]):
    """Abstract base class for reading items."""
    
    @abstractmethod
    def read(self) -> Optional[T]:
        """Read the next item. Return None when no more items are available."""
        pass

class ItemProcessor(ABC, Generic[T, U]):
    """Abstract base class for processing items."""
    
    @abstractmethod
    def process(self, item: T) -> Optional[U]:
        """Process an item. Return None to filter out the item."""
        pass

class ItemWriter(ABC, Generic[U]):
    """Abstract base class for writing items."""
    
    @abstractmethod
    def write(self, items: List[U]) -> None:
        """Write a chunk of items."""
        pass

# Concrete implementations for common use cases

class ListItemReader(ItemReader[T]):
    """Reads items from a list."""
    
    def __init__(self, items: List[T]):
        self.items = items
        self.index = 0
    
    def read(self) -> Optional[T]:
        if self.index < len(self.items):
            item = self.items[self.index]
            self.index += 1
            return item
        return None

class CallableItemReader(ItemReader[T]):
    """Reads items using a callable that returns an iterator."""
    
    def __init__(self, callable_source: Callable[[], Iterator[T]]):
        self.iterator = callable_source()
    
    def read(self) -> Optional[T]:
        try:
            return next(self.iterator)
        except StopIteration:
            return None

class FunctionItemProcessor(ItemProcessor[T, U]):
    """Processes items using a function."""
    
    def __init__(self, process_func: Callable[[T], Optional[U]]):
        self.process_func = process_func
    
    def process(self, item: T) -> Optional[U]:
        return self.process_func(item)

class ListItemWriter(ItemWriter[U]):
    """Writes items to a list (for testing/demo purposes)."""
    
    def __init__(self, target_list: List[U]):
        self.target_list = target_list
    
    def write(self, items: List[U]) -> None:
        self.target_list.extend(items)

class CallableItemWriter(ItemWriter[U]):
    """Writes items using a callable."""
    
    def __init__(self, write_func: Callable[[List[U]], None]):
        self.write_func = write_func
    
    def write(self, items: List[U]) -> None:
        self.write_func(items)

class PassThroughProcessor(ItemProcessor[T, T]):
    """A processor that doesn't modify items (identity function)."""
    
    def process(self, item: T) -> Optional[T]:
        return item
