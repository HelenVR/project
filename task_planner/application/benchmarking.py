import asyncio
import time
from functools import wraps
from loguru import logger


def measure_time(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        time_elapsed = time.perf_counter() - start_time
        logger.debug(f"Function {func.__name__} took {time_elapsed:0.3f} seconds")
        return result

    @wraps(func)
    async def async_wrapped(*args, **kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        time_elapsed = time.perf_counter() - start_time
        logger.debug(f"Function {func.__name__} took {time_elapsed:0.3f} seconds")
        return result

    return async_wrapped if asyncio.iscoroutinefunction(func) else wrapped


