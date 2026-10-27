import copy
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from django.core.handlers.wsgi import WSGIRequest
from rest_framework.request import Request

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])

LOG_MASK = "******"
SECRET_KEYS = frozenset({"code", "verifPath", "token"})


def _is_secret_key(key: object) -> bool:
    if not isinstance(key, str):
        return False
    return key in SECRET_KEYS or "password" in key.lower()


def _mask_secrets(params: Any) -> None:
    """Replace the value of each secret key of params with the mask."""
    if not hasattr(params, "keys") or not hasattr(params, "__setitem__"):
        return
    for key in list(params.keys()):
        if _is_secret_key(key):
            params[key] = LOG_MASK


def log_filter(
    request: Request | WSGIRequest,
    message: str, *args: Any,
) -> str:
    """Filter request info for logging."""
    if len(args) > 0:
        message = message % args
    request_method: str = getattr(request, "method", "-")
    path_info: str = getattr(request, "path_info", "-")
    username: str = "guest"
    if request.user.is_authenticated:
        user = request.user
        username = user.email  # type: ignore

    # Headers
    meta: dict[str, Any] = getattr(request, "META", {})
    remote_addr: str = meta.get("REMOTE_ADDR", "-")
    data: Any = copy.deepcopy(getattr(request, "data", "-"))
    query_params: Any = copy.deepcopy(getattr(request, "query_params", "-"))
    _mask_secrets(data)
    _mask_secrets(query_params)

    return (
        f"user: {username}; remote addr: {remote_addr}; "
        f"method: {request_method}; path: {path_info}; "
        f"data: {data}; query_params: {query_params}; message: <{message}>"
    )


def request_logging(logger: logging.Logger) -> Callable[[F], F]:
    """Automatically log request info on views."""

    def logging_decorator(func: F) -> F:
        @wraps(func)
        def func_wrapper(
            self: Any,
            request: Request | WSGIRequest,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            message_parts: list[str] = []
            if args:
                message_parts.append(f"{args}")
            if kwargs:
                message_parts.append(f"{kwargs}")
            message: str = "; ".join(message_parts)
            logger.info(log_filter(request, message).strip())

            return func(self, request, *args, **kwargs)

        return func_wrapper  # type: ignore[return-value]

    return logging_decorator


def request_logging_function_view(logger: logging.Logger) -> Callable[[F], F]:
    """Automatically log request info on view functions."""

    def logging_decorator(func: F) -> F:
        @wraps(func)
        def func_wrapper(
            request: Request | WSGIRequest,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            message_parts: list[str] = []
            if args:
                message_parts.append(f"{args}")
            if kwargs:
                message_parts.append(f"{kwargs}")
            message: str = "; ".join(message_parts)
            logger.info(log_filter(request, message).strip())

            return func(request, *args, **kwargs)

        return func_wrapper  # type: ignore[return-value]

    return logging_decorator
