import time
import queue
import logging
from contextlib import closing
from dae.query_variants.query_runners import QueryRunner

logger = logging.getLogger(__name__)


class SqlQueryRunner(QueryRunner):
    """Run a query in a separate thread."""

    def __init__(self, connection_pool, query, deserializer=None):
        super().__init__(deserializer=deserializer)

        self.connection_pool = connection_pool
        self.query = query

    def connect(self):
        """Connect to the connection pool and return the connection."""
        started = time.time()
        while True:
            try:
                connection = self.connection_pool.connect()
                return connection
            except TimeoutError:
                elapsed = time.time() - started
                logger.debug(
                    "runner (%s) timeout in connect; elapsed %0.2fsec",
                    self.study_id, elapsed)
                if self.closed():
                    logger.info(
                        "runner (%s) closed before connection established "
                        "after %0.2fsec",
                        self.study_id, elapsed)
                    return None

    def run(self):
        """Execute the query and enqueue the resulting rows."""
        started = time.time()
        if self.closed():
            logger.info(
                "impala runner (%s) closed before executing...",
                self.study_id)
            return

        logger.debug(
            "impala runner (%s) started; "
            "connectio pool: %s",
            self.study_id, self.connection_pool.status())

        connection = self.connect()

        if connection is None:
            self._finalize(started)
            return

        with closing(connection) as connection:
            elapsed = time.time() - started
            logger.debug(
                "runner (%s) waited %0.2fsec for connection",
                self.study_id, elapsed)
            with connection.cursor() as cursor:
                try:
                    if self.closed():
                        logger.info(
                            "runner (%s) closed before execution "
                            "after %0.2fsec",
                            self.study_id, elapsed)
                        self._finalize(started)
                        return

                    cursor.execute_async(self.query)
                    self._wait_cursor_executing(cursor)

                    while not self.closed():
                        row = cursor.fetchone()
                        if row is None:
                            break
                        val = self.deserializer(row)

                        if val is None:
                            continue

                        self._put_value_in_result_queue(val)

                        if self.closed():
                            logger.debug(
                                "query runner (%s) closed while iterating",
                                self.study_id)
                            break

                except Exception as ex:  # pylint: disable=broad-except
                    logger.debug(
                        "exception in runner (%s) run: %s",
                        self.study_id, type(ex), exc_info=True)
                finally:
                    logger.debug(
                        "runner (%s) closing connection", self.study_id)

        self._finalize(started)

    def _put_value_in_result_queue(self, val):
        no_interest = 0
        while True:
            try:
                self._result_queue.put(val, timeout=0.1)
                break
            except queue.Full:
                logger.debug(
                    "runner (%s) nobody interested",
                    self.study_id)

                if self.closed():
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

    def _wait_cursor_executing(self, cursor):
        while True:
            if self.closed():
                logger.debug(
                    "query runner (%s) closed while executing",
                    self.study_id)
                break
            if not cursor.is_executing():
                logger.debug(
                    "query runner (%s) execution finished",
                    self.study_id)
                break
            time.sleep(0.1)

    def _finalize(self, started):
        with self._status_lock:
            self._done = True
        elapsed = time.time() - started
        logger.debug("runner (%s) done in %0.3f sec", self.study_id, elapsed)
        logger.debug("connection pool: %s", self.connection_pool.status())