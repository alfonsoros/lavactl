"""
Copyright (c) 2017 Siemens AG
Author: Alfonso Ros Dos Santos

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

import signal
import logging
from functools import wraps

class TimeoutError(Exception):
    pass

def timeout(seconds=10, logger=None):
	"""Handle the timeout of a submitted job"""
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
