import time
import logging
from contextlib import closing
from dae.query_variants.query_runners import QueryRunner

logger = logging.getLogger(__name__)


class ImpalaQueryRunner(QueryRunner):
    """Run a Impala query in a separate thread."""

    def __init__(self, connection_factory, query, deserializer=None):
        super().__init__(deserializer=deserializer)

        self.connection_pool = connection_factory
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
                    logger.error(
                        "exception in runner (%s) run: %s",
                        self.study_id, type(ex), exc_info=True)
                    self._put_value_in_result_queue(ex)
                finally:
                    logger.debug(
                        "runner (%s) closing connection", self.study_id)

        self._finalize(started)

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
