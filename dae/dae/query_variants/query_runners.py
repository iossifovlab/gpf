import abc
import threading
import logging
import queue
import time

from concurrent.futures import ThreadPoolExecutor


logger = logging.getLogger(__name__)


class QueryRunner(abc.ABC):
    """Run a query in the backround using the provided executor."""

    def __init__(self, deserializer=None):
        super().__init__()

        self._status_lock = threading.RLock()
        self._closed = False
        self._started = False
        self._done = False
        self.timestamp = None

        self._result_queue = None
        self._future = None
        self.study_id = None

        if deserializer is not None:
            self.deserializer = deserializer
        else:
            self.deserializer = lambda v: v

    def adapt(self, adapter_func):
        func = self.deserializer

        self.deserializer = lambda v: adapter_func(func(v))

    def started(self):
        with self._status_lock:
            return self._started

    def start(self, executor):
        with self._status_lock:
            assert self._result_queue is not None

            self._future = executor.submit(self.run)
            self._started = True
            self.timestamp = time.time()

    def closed(self):
        with self._status_lock:
            return self._closed

    def close(self):
        elapsed = time.time() - self.timestamp
        logger.debug("closing runner after %0.3f", elapsed)
        with self._status_lock:
            if self._started:
                self._future.cancel()
            self._closed = True

    def done(self):
        with self._status_lock:
            return self._done

    @abc.abstractmethod
    def run(self):
        pass

    def _set_future(self, future):
        self._future = future

    def _set_result_queue(self, result_queue):
        self._result_queue = result_queue


class QueryResult:
    """Run a list of queries in the background.

    The result of the queries is enqueued on result_queue
    """

    def __init__(self, runners: list[QueryRunner], limit=-1):
        self.result_queue: queue.Queue = queue.Queue(maxsize=1_000)

        if limit is None:
            limit = -1
        self.limit = limit
        self._counter = 0
        self.timestamp = time.time()

        self.runners = runners
        for runner in self.runners:
            assert runner._result_queue is None
            runner._set_result_queue(self.result_queue)
        self.executor = ThreadPoolExecutor(max_workers=len(runners))

    def done(self):
        if self.limit >= 0 and self._counter >= self.limit:
            logger.debug("limit done %d >= %d", self._counter, self.limit)
            return True
        if all(r.done() for r in self.runners):
            return True
        return False

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            try:
                item = self.result_queue.get(timeout=0.1)
                self._counter += 1
                return item
            except queue.Empty as exp:
                if not self.done():
                    return None
                logger.debug("result done")
                raise StopIteration() from exp

    def get(self, timeout=0):
        """Pop the next entry from the queue.

        Return None if the queue is still empty after timeout seconds.
        """
        try:
            row = self.result_queue.get(timeout=timeout)
            return row
        except queue.Empty as exp:
            if self.done():
                raise StopIteration() from exp
            return None

    def start(self):
        self.timestamp = time.time()
        for runner in self.runners:
            runner.start(self.executor)
        time.sleep(0.1)

    def close(self):
        """Gracefully close and dispose of resources."""
        for runner in self.runners:
            try:
                runner.close()
            except Exception as ex:  # pylint: disable=broad-except
                logger.info(
                    "exception in result close: %s", type(ex), exc_info=True)
        while not self.result_queue.empty():
            self.result_queue.get()

        logger.debug("closing thread pool executor")
        self.executor.shutdown(wait=True)
        elapsed = time.time() - self.timestamp
        logger.debug("result closed after %0.3f", elapsed)