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
    data = getattr(request, "data", "-")
    query_params = getattr(request, "query_params", "-")

    return (
        f"user: {username}; remote addr: {remote_addr}; "
        f"method: {request_method}; path: {path_info}; "
        f"data: {data}; query_params: {query_params}; message: <{message}>"
    )


def request_logging(logger):
    """Automatically log request info on views"""

    def logging_decorator(func):
        @wraps(func)
        def func_wrapper(self, request, *args, **kwargs):
            message = []
            if args:
                message.append(f"{args}")
            if kwargs:
                message.append(f"{kwargs}")
            message = "; ".join(message)
            logger.info(log_filter(request, message).strip())

            return func(self, request, *args, **kwargs)

        return func_wrapper

    return logging_decorator


def request_logging_function_view(logger):
    """Automatically log request info on view functions"""

    def logging_decorator(func):
        @wraps(func)
        def func_wrapper(request, *args, **kwargs):
            message = []
            if args:
                message.append(f"{args}")
            if kwargs:
                message.append(f"{kwargs}")
            message = "; ".join(message)
            logger.info(log_filter(request, message).strip())

            return func(request, *args, **kwargs)

        return func_wrapper

    return logging_decorator
