import signal
import logging
from functools import wraps

class TimeoutError(Exception):
    pass

def timeout(seconds=10, logger=None):
    logger = logger or logging.getLogger(__name__ + '.timeout')
    def decorator(func):
        @wraps(func)
        def set_timeout_alarm(*args, **kwargs):

            def raise_timeout(*args, **kwargs):
                logger.warning("Timeout exception")
                raise TimeoutError()

            signal.signal(signal.SIGALRM, raise_timeout)
            signal.alarm(seconds)
            result = func(*args, **kwargs)
            signal.alarm(0)
            return result
        return set_timeout_alarm
    return decorator
