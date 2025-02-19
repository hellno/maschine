import time
import functools
import logging

def measure_time(func):
    """Measure the execution time of a function and log it."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        logging.info(f"Function '{func.__name__}' took {elapsed_time:.3f} seconds to execute.")
        return result
    return wrapper

def format_elapsed_time(seconds: float) -> str:
    """Format elapsed time in seconds to a human-readable string."""
    if seconds >= 60:
        minutes = int(seconds // 60)
        seconds = seconds % 60
        return f"{minutes} minute{'s' if minutes != 1 else ''}, {seconds:.3f} seconds"
    return f"{seconds:.3f} seconds"
