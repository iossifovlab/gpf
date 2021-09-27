import abc
import threading
import logging
import queue
import time

from concurrent.futures import ThreadPoolExecutor


logger = logging.getLogger(__name__)


class QueryRunner(abc.ABC):

    def __init__(self, deserializer=None):
        super(QueryRunner, self).__init__()

        self._status_lock = threading.Lock()
        self._closed = False
        self._started = False
        self._done = False

        self._result_queue = None
        self._future = None

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
        logger.debug(f"closing runner after {elapsed:0.3f}")
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
    def __init__(self, runners, limit=-1):
        self.result_queue = queue.Queue(maxsize=1_000)

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
            logger.debug(f"limit done {self._counter} >= {self.limit}")
            return True
        if all([r.done() for r in self.runners]):
            return True

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            try:
                item = self.result_queue.get(timeout=0.1)
                self._counter += 1
                return item
            except queue.Empty:
                if not self.done():
                    return None
                else:
                    logger.debug("result done")
                    raise StopIteration()

    def get(self, timeout=0):
        try:
            row = self.result_queue.get(timeout=timeout)
            return row
        except queue.Empty:
            if self.done():
                raise StopIteration()

    def start(self):
        self.timestamp = time.time()
        for runner in self.runners:
            runner.start(self.executor)
        time.sleep(0.1)

    def close(self):
        for runner in self.runners:
            try:
                runner.close()
            except BaseException as ex:
                logger.info(
                    f"exception in result close: {type(ex)}", exc_info=True)
        while not self.result_queue.empty():
            self.result_queue.get()

        logger.debug("closing thread pool executor")
        self.executor.shutdown(wait=True)
        elapsed = time.time() - self.timestamp
        logger.debug(f"result closed after {elapsed:0.3f}")
