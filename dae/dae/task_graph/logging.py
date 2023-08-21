import re
import uuid
import logging
from typing import Any, cast, Optional

from dae.utils import fs_utils


class FsspecHandler(logging.StreamHandler):
    """Class to create fsspec based logging handler."""

    def __init__(self, logfile: str):
        fs, logpath = fs_utils.url_to_fs(logfile)
        stream = fs.open(logpath, "w")
        super().__init__(stream=stream)

    def close(self) -> None:
        """Close the stream.

        Copied from logging.FileHandler.close().
        """
        self.acquire()
        try:
            try:
                if self.stream:
                    try:
                        self.flush()
                    finally:
                        stream = self.stream
                        self.stream = None
                        stream.close()
            finally:
                # Issue #19523: call unconditionally to
                # prevent a handler leak when delay is set
                # Also see Issue #42378: we also rely on
                # self._closed being set to True there
                logging.StreamHandler.close(self)
        finally:
            self.release()


def ensure_log_dir(**kwargs: Any) -> str:
    """Ensure logging directory exists."""
    log_dir = kwargs.get("log_dir")
    if log_dir is not None:
        log_dir = fs_utils.abspath(log_dir)
        if not fs_utils.exists(log_dir):
            fs, path = fs_utils.url_to_fs(log_dir)
            fs.mkdir(path, exists_ok=True)
    return cast(str, log_dir)


def configure_task_logging(
    log_dir: Optional[str], task_id: str, verbosity: int
) -> logging.Handler:
    """Configure and return task logging hadnler."""
    if log_dir is None:
        return logging.NullHandler()

    if verbosity == 1:
        loglevel = logging.INFO
    elif verbosity == 2:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.WARNING

    logfile = fs_utils.join(log_dir, f"log_{task_id}.log")

    handler = FsspecHandler(logfile)
    formatter = logging.Formatter(
        f"{task_id}: %(asctime)s %(name)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    handler.setLevel(loglevel)

    return handler


RE_TASK_ID = re.compile(r"[\. /,()\-:;]")


def safe_task_id(task_id: str) -> str:
    result = RE_TASK_ID.sub("_", task_id)
    if len(result) <= 200:
        return result
    result = result[:150]
    return f"{result}_{uuid.uuid1()}"
