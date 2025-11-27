"""
Skip Policy and Exception Handling

This module provides skip logic for handling exceptions during batch processing.
Items that cause exceptions can be skipped up to a configurable limit.
"""

from typing import Set, Type, Optional
from abc import ABC, abstractmethod

class SkipPolicy(ABC):
    """Abstract base class for skip policies."""
    
    @abstractmethod
    def should_skip(self, exception: Exception, skip_count: int) -> bool:
        """Determine if an exception should be skipped."""
        pass

class NeverSkipPolicy(SkipPolicy):
    """Never skip any exceptions - fail immediately."""
    
    def should_skip(self, exception: Exception, skip_count: int) -> bool:
        return False

class AlwaysSkipPolicy(SkipPolicy):
    """Always skip exceptions (dangerous - use with caution)."""
    
    def should_skip(self, exception: Exception, skip_count: int) -> bool:
        return True

class LimitCheckingSkipPolicy(SkipPolicy):
    """Skip exceptions up to a specified limit."""
    
    def __init__(self, skip_limit: int = 10, skippable_exceptions: Optional[Set[Type[Exception]]] = None):
        self.skip_limit = skip_limit
        self.skippable_exceptions = skippable_exceptions or {Exception}
    
    def should_skip(self, exception: Exception, skip_count: int) -> bool:
        # Check if we've exceeded the skip limit
        if skip_count >= self.skip_limit:
            return False
        
        # Check if this exception type is skippable
        for exc_type in self.skippable_exceptions:
            if isinstance(exception, exc_type):
                return True
        
        return False

class ExceptionClassifierSkipPolicy(SkipPolicy):
    """Skip only specific exception types, with optional limit."""
    
    def __init__(self, skippable_exceptions: Set[Type[Exception]], skip_limit: Optional[int] = None):
        self.skippable_exceptions = skippable_exceptions
        self.skip_limit = skip_limit
    
    def should_skip(self, exception: Exception, skip_count: int) -> bool:
        # Check limit if specified
        if self.skip_limit is not None and skip_count >= self.skip_limit:
            return False
        
        # Check if exception type is skippable
        for exc_type in self.skippable_exceptions:
            if isinstance(exception, exc_type):
                return True
        
        return False

# Common exception types for skipping
class SkippableException(Exception):
    """Base class for exceptions that should be skipped."""
    pass

class ValidationException(SkippableException):
    """Data validation failed."""
    pass

class ParseException(SkippableException):
    """Data parsing failed."""
    pass

class TransformException(SkippableException):
    """Data transformation failed."""
    pass
