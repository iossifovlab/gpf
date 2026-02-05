from __future__ import annotations

import abc
import logging
import queue
import threading
import time
from collections.abc import Callable, Sequence
from concurrent.futures import Executor, Future, ThreadPoolExecutor
from typing import Any

logger = logging.getLogger(__name__)
QUEUE_TIMEOUT = 0.1


class QueryRunner(abc.ABC):
    """Run a query in the backround using the provided executor."""

    NOBODY_INTEREST_THRESHOLD = 1_000
    NOBODY_INTEREST_LOG_INTERVAL = 100

    def __init__(self, **kwargs: Any):
        super().__init__()

        self._status_lock = threading.RLock()
        self._closed = False
        self._started = False
        self._done = False
        self.timestamp = time.time()

        self._result_queue: queue.Queue | None = None
        self._future: Future | None = None
        self.study_id: str | None = None

        deserializer = kwargs.get("deserializer")
        if deserializer is not None:
            self.deserializer = deserializer
        else:
            self.deserializer = lambda v: v

    def set_study_id(self, study_id: str) -> None:
        self.study_id = study_id

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
        logger.debug("(%s) closing runner after %0.3f", self.study_id, elapsed)
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
        """Run the query and enqueue results in the result queue."""

    @property
    def result_queue(self) -> queue.Queue | None:
        return self._result_queue

    def set_result_queue(self, result_queue: queue.Queue) -> None:
        assert self._result_queue is None
        assert result_queue is not None
        self._result_queue = result_queue

    def put_value_in_result_queue(self, val: Any) -> None:
        """Put a value in the result queue.

        The result queue is blocking, so it will wait until there is space
        for the new value. So it causes backpressure on the QueryRunners.
        """
        assert self._result_queue is not None

        no_interest = 0
        while True:
            try:
                self._result_queue.put(val, timeout=QUEUE_TIMEOUT)
                no_interest = 0
                break
            except queue.Full:
                no_interest += 1

                if self.is_closed():
                    logger.info(
                        "runner (%s) closed while putting value in"
                        " result queue",
                        self.study_id)
                    break
                if no_interest % self.NOBODY_INTEREST_LOG_INTERVAL == 0:
                    logger.warning(
                        "runner (%s) nobody interested %s",
                        self.study_id, no_interest)
                if no_interest > self.NOBODY_INTEREST_THRESHOLD:
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
    CHECK_DONE_VERBOSITY = 20

    def __init__(
        self, executor: ThreadPoolExecutor,
        runners: Sequence[QueryRunner], *,
        limit: int | None = -1,
        max_queue_size: int = 5_000,
    ):
        self.result_queue: queue.Queue = queue.Queue(maxsize=max_queue_size)

        if limit is None:
            limit = -1
        self.limit = limit
        self._counter = 0
        self.timestamp = time.time()
        self._exceptions: list[Exception] = []

        self.runners = runners
        for runner in self.runners:
            assert runner.result_queue is None
            runner.set_result_queue(self.result_queue)
        self.executor = executor
        self._is_done_check = 0

    def is_done(self) -> bool:
        """Check if the query result is done."""
        self._is_done_check += 1
        if self.limit >= 0 and self._counter >= self.limit:
            logger.debug("limit done %d >= %d", self._counter, self.limit)
            return True
        if all(r.is_done() for r in self.runners):
            logger.debug("all runners are done... exiting...")
            logger.info("returned variants: %s", self._counter)
            return True
        if self._is_done_check > self.CHECK_DONE_VERBOSITY:
            self._is_done_check = 0
            logger.debug(
                "studies not done: %s",
                [r.study_id for r in self.runners if not r.is_done()])
        return False

    def __iter__(self) -> QueryResult:
        return self

    def __next__(self) -> Any:
        while True:
            try:
                item = self.result_queue.get(timeout=QUEUE_TIMEOUT)

                if isinstance(item, Exception):
                    self._exceptions.append(item)
                    continue
                self._counter += 1
                if self.limit > 0 and self._counter > self.limit:
                    logger.debug(
                        "limit reached %d > %d", self._counter, self.limit)
                    raise StopIteration
            except queue.Empty as exp:
                if not self.is_done():
                    return None
                raise StopIteration from exp
            return item

    def start(self) -> None:
        self.timestamp = time.time()
        for runner in self.runners:
            runner.start(self.executor)
        time.sleep(0.1)

    def close(self) -> None:
        """Gracefully close and dispose of resources."""
        logger.info("closing query result...")
        logger.info("closing %s query runners", len(self.runners))
        for runner in self.runners[::-1]:
            # pylint: disable=broad-except
            try:
                runner.close()
                logger.debug("runner %s closed", runner.study_id)
            except Exception as ex:  # noqa: BLE001
                logger.info(
                    "exception in result close: %s", type(ex), exc_info=True)
        logger.debug("emptying result queue %s", self.result_queue.qsize())
        while not self.result_queue.empty():
            item = self.result_queue.get()
            if isinstance(item, Exception):
                self._exceptions.append(item)

        elapsed = time.time() - self.timestamp
        logger.debug("result closed after %0.3f", elapsed)
        if self._exceptions:
            for error in self._exceptions:
                logger.error(
                    "unexpected exception in query result: %s", error,
                    stack_info=True)
            raise OSError(self._exceptions[0])
