import traceback
import logging

from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Queue

from typing import Any


logger = logging.getLogger(__name__)


class ImpalaQueryRunner:

    def __init__(self, connection, query, result_queue):
        super(ImpalaQueryRunner, self).__init__()
        self.connection = connection
        self.cursor = connection.cursor()
        self.query = query
        self.result_queue = result_queue
        self._future = None

    def run(self):
        try:
            self.cursor.execute(self.query)
            while not self.cursor._closed:
                row = self.cursor.fetchone()
                if self.result_queue.full():
                    logger.debug(
                        f"queue is full ({self.result_queue.qsize()}); "
                        f"going to block")
                self.result_queue.put(row)
        except BaseException as ex:
            logger.debug(
                f"exception in runner run: {type(ex)}", exc_info=True)
        finally:
            self.connection.close()
        logger.debug("runner done")

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        self.run()

    def close(self):
        try:
            self.cursor.close()
        except BaseException as ex:
            logger.debug(
                f"exception in runner close: {type(ex)}", exc_info=True)
        logger.debug("runner closed")

    def _set_future(self, future):
        self._future = future

    def done(self):
        return self._future.done()


class ImpalaQueryResult:
    def __init__(self, result_queue, runners):
        self.result_queue = result_queue
        self.runners = runners

    def done(self):
        return all([r.done() for r in self.runners])

    def __iter__(self):
        return self

    def __next__(self):
        if self.done():
            print("don't even try; runner done")
            raise StopIteration()

        try:
            row = self.result_queue.get(timeout=0.1)
            return row
        except Empty:
            if self.done():
                print("result done")
                raise StopIteration()

    def get(self, timeout=0):
        try:
            row = self.result_queue.get(timeout=timeout)
            return row
        except Empty:
            if self.done():
                raise StopIteration()

    def close(self):
        for runner in self.runners:
            try:
                runner.close()
            except BaseException as ex:
                print("exception in result close:", type(ex))
                traceback.print_tb(ex.__traceback__)
        while not self.result_queue.empty():
            self.result_queue.get()


class ImpalaQueryExecutor:
    def __init__(self, impala_helpers):
        self.impala_helpers = impala_helpers
        self.executor = ThreadPoolExecutor(max_workers=6)

    def _submit(self, query, result_queue):
        connection = self.impala_helpers.connection()
        runner = ImpalaQueryRunner(connection, query, result_queue)
        future = self.executor.submit(runner)
        runner._set_future(future)
        return runner

    def submit(self, query):
        result_queue = Queue(maxsize=1_000)
        runner = self._submit(query, result_queue)
        result = ImpalaQueryResult(result_queue, [runner])
        return result

    def map(self, queries):
        result_queue = Queue(maxsize=1_000)
        runners = []
        for query in queries:
            runner = self._submit(query, result_queue)
            runners.append(runner)

        result = ImpalaQueryResult(result_queue, runners)
        return result
