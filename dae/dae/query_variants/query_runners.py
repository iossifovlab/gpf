from __future__ import annotations

import abc
import threading
import logging
import queue
import time
from typing import Optional, Any, Callable

from concurrent.futures import ThreadPoolExecutor, Future, Executor


logger = logging.getLogger(__name__)


class QueryRunner(abc.ABC):
    """Run a query in the backround using the provided executor."""

    def __init__(self, **kwargs: Any):
        super().__init__()

        self._status_lock = threading.RLock()
        self._closed = False
        self._started = False
        self._done = False
        self.timestamp = time.time()

        self._result_queue: Optional[queue.Queue] = None
        self._future: Optional[Future] = None
        self.study_id = None

        deserializer = kwargs.get("deserializer")
        if deserializer is not None:
            self.deserializer = deserializer
        else:
            self.deserializer = lambda v: v

    def adapt(self, adapter_func: Callable[[Any], Any]) -> None:
        func = self.deserializer

        self.deserializer = lambda v: adapter_func(func(v))

    def is_started(self) -> bool:
        with self._status_lock:
            return self._started

    def start(self, executor: Executor) -> None:
        with self._status_lock:
            assert self._result_queue is not None

            self._future = executor.submit(self.run)
            self._started = True
            self.timestamp = time.time()

    def is_closed(self) -> bool:
        with self._status_lock:
            return self._closed

    def close(self) -> None:
        """Close query runner."""
        elapsed = time.time() - self.timestamp
        logger.debug("closing runner after %0.3f", elapsed)
        with self._status_lock:
            if not self._closed and self._started:
                assert self._future is not None
                self._future.cancel()
            self._closed = True

    def is_done(self) -> bool:
        with self._status_lock:
            return self._done

    @abc.abstractmethod
    def run(self) -> None:
        pass

    def _set_future(self, future: Future) -> None:
        self._future = future

    def _set_result_queue(self, result_queue: queue.Queue) -> None:
        self._result_queue = result_queue

    def _put_value_in_result_queue(self, val: Any) -> None:
        assert self._result_queue is not None

        no_interest = 0
        while True:
            try:
                self._result_queue.put(val, timeout=0.1)
                break
            except queue.Full:
                logger.debug(
                    "runner (%s) nobody interested",
                    self.study_id)

                if self.is_closed():
                    break
                no_interest += 1
                if no_interest % 1_000 == 0:
                    logger.warning(
                        "runner (%s) nobody interested %s",
                        self.study_id, no_interest)
                if no_interest > 5_000:
                    logger.warning(
                        "runner (%s) nobody interested %s"
                        "closing...",
                        self.study_id, no_interest)
                    self.close()
                    break


class QueryResult:
    """Run a list of queries in the background.

    The result of the queries is enqueued on result_queue
    """

    def __init__(self, runners: list[QueryRunner], limit: int = -1):
        self.result_queue: queue.Queue = queue.Queue(maxsize=1_000)

        if limit is None:
            limit = -1
        self.limit = limit
        self._counter = 0
        self.timestamp = time.time()
        self._exceptions: list[Exception] = []

        self.runners = runners
        for runner in self.runners:
            assert runner._result_queue is None
            runner._set_result_queue(self.result_queue)
        self.executor = ThreadPoolExecutor(max_workers=len(runners))

    def done(self) -> bool:
        if self.limit >= 0 and self._counter >= self.limit:
            logger.debug("limit done %d >= %d", self._counter, self.limit)
            return True
        if all(r.is_done() for r in self.runners):
            return True
        return False

    def __iter__(self) -> QueryResult:
        return self

    def __next__(self) -> Any:
        while True:
            try:
                item = self.result_queue.get(timeout=0.1)
                if isinstance(item, Exception):
                    self._exceptions.append(item)
                    continue
                self._counter += 1
                return item
            except queue.Empty as exp:
                if not self.done():
                    return None
                logger.debug("result done")
                raise StopIteration() from exp

    def get(self, timeout: float = 0.0) -> Any:
        """Pop the next entry from the queue.

        Return None if the queue is still empty after timeout seconds.
        """
        try:
            row = self.result_queue.get(timeout=timeout)
            if isinstance(row, Exception):
                self._exceptions.append(row)
                return None
            return row
        except queue.Empty as exp:
            if self.done():
                raise StopIteration() from exp
            return None

    def start(self) -> None:
        self.timestamp = time.time()
        for runner in self.runners:
            runner.start(self.executor)
        time.sleep(0.1)

    def close(self) -> None:
        """Gracefully close and dispose of resources."""
        for runner in self.runners:
            try:
                runner.close()
            except Exception as ex:  # pylint: disable=broad-except
                logger.info(
                    "exception in result close: %s", type(ex), exc_info=True)
        while not self.result_queue.empty():
            item = self.result_queue.get()
            if isinstance(item, Exception):
                self._exceptions.append(item)

        logger.debug("closing thread pool executor")
        self.executor.shutdown(wait=True)
        elapsed = time.time() - self.timestamp
        logger.debug("result closed after %0.3f", elapsed)
        if self._exceptions:
            for error in self._exceptions:
                logger.error(
                    "unexpected exception in query result: %s", error,
                    exc_info=True, stack_info=True)
            raise IOError(self._exceptions[0])
