import functools
import logging
from typing import Any, Callable, Optional

logging.basicConfig(level=logging.INFO)

class APIError(Exception):
    """Raised when an external API fails after retries."""
    pass

class NoMediaFoundError(Exception):
    pass

def fallback(default_value: Optional[Any] = None, retry: int = 1):
    """Decorator: retry then fallback to a default value or re‑raise."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retry + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.warning(f"{func.__name__} attempt {attempt+1} failed: {e}")
                    if attempt == retry:
                        if default_value is not None:
                            return default_value
                        raise
            return None
        return wrapper
    return decorator