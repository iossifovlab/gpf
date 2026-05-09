import os
from collections.abc import Callable


def validate_path(
    field: str, value: str, error: Callable,
) -> None:
    if not os.path.isabs(value):
        error(field, f"path <{value}> is not an absolute path")


def validate_existing_path(
    field: str, value: str, error: Callable,
) -> None:
    if not os.path.isabs(value):
        error(field, f"path <{value}> is not an absolute path!")
    if not os.path.exists(value):
        error(field, f"path <{value}> does not exist!")
