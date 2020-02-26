"""
Created on Jun 12, 2015

@author: lubo
"""
import logging
from functools import wraps

LOGGER = logging.getLogger("wdae.api")


def log_filter(request, message):
    request_method = getattr(request, "method", "-")
    path_info = getattr(request, "path_info", "-")
    username = "guest"
    if request.user.is_authenticated:
        username = request.user.email

    # Headers
    META = getattr(request, "META", {})
    remote_addr = META.get("REMOTE_ADDR", "-")
    # server_protocol = META.get('SERVER_PROTOCOL', '-')
    # http_user_agent = META.get('HTTP_USER_AGENT', '-')
    return (
        f"user: {username}; remote addr: {remote_addr}; "
        + f"method: {request_method}; path: {path_info}; {message}"
    )


def request_logging(_LOGGER):
    """Automatically log request info on views"""

    def request_logging_decorator(func):
        @wraps(func)
        def func_wrapper(self, request, *args, **kwargs):
            _LOGGER.info(log_filter(request, "").strip())

            return func(self, request, *args, **kwargs)

        return func_wrapper

    return request_logging_decorator


def request_logging_function_view(_LOGGER):
    """Automatically log request info on view functions"""

    def request_logging_decorator(func):
        @wraps(func)
        def func_wrapper(request, *args, **kwargs):
            _LOGGER.info(log_filter(request, "").strip())

            return func(request, *args, **kwargs)

        return func_wrapper

    return request_logging_decorator
