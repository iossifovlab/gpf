import time
import logging
from contextlib import closing

import impala
from sqlalchemy import exc

# from dae.utils.debug_closing import closing
from dae.query_variants.query_runners import QueryRunner

logger = logging.getLogger(__name__)


class ImpalaQueryRunner(QueryRunner):
    """Run a Impala query in a separate thread."""

    def __init__(self, connection_factory, query, deserializer=None):
        super().__init__(deserializer=deserializer)

        self.connection_pool = connection_factory
        self.query = query
        self._counter = 0

    def connect(self):
        """Connect to the connection pool and return the connection."""
        started = time.time()
        logger.debug("(%s) going to conect", self.study_id)
        attempt = 0
        while True:
            try:
                attempt += 1
                logger.debug(
                    "(%s) trying to connect; attemp %s; %s", self.study_id,
                    attempt, self.connection_pool.status())
                connection = self.connection_pool.connect()
                logger.debug(
                    "(%s) connection created; pool status %s",
                    self.study_id,
                    self.connection_pool.status())
                return connection
            except exc.TimeoutError:
                elapsed = time.time() - started
                logger.debug(
                    "runner (%s) timeout in connect; elapsed %0.2fsec",
                    self.study_id, elapsed)
                if self.is_closed():
                    logger.info(
                        "runner (%s) closed before connection established "
                        "after %0.2fsec",
                        self.study_id, elapsed)
                    return None
            except Exception:  # pylint: disable=broad-except
                logger.error(
                    "(%s) unexpected exception", self.study_id, exc_info=True)
                return None

    NO_DATA_LIMIT = 1_000

    def run(self) -> None:
        """Execute the query and enqueue the resulting rows."""
        started = time.time()
        if self.is_closed():
            logger.info(
                "impala runner (%s) closed before executing...",
                self.study_id)
            return

        logger.debug(
            "(%s) impala runner started; trying to connect... "
            "connection pool: %s",
            self.study_id, self.connection_pool.status())

        connection = self.connect()
        logger.debug(
            "(%s) connected; connection pool: %s",
            self.study_id, self.connection_pool.status())

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
                    if self.is_closed():
                        logger.info(
                            "runner (%s) closed before execution "
                            "after %0.2fsec",
                            self.study_id, elapsed)
                        self._finalize(started)
                        return

                    cursor.execute_async(self.query)
                    self._wait_cursor_executing(cursor)

                    while not self.is_closed():
                        row = cursor.fetchone()
                        if row is None:
                            break
                        val = self.deserializer(row)

                        if val is None:
                            continue

                        self._put_value_in_result_queue(val)
                        self._counter += 1

                        if self.is_closed():
                            logger.debug(
                                "query runner (%s) closed while iterating",
                                self.study_id)
                            break

                except Exception as ex:  # pylint: disable=broad-except
                    logger.error(
                        "exception in runner (%s) run: %s",
                        self.study_id, type(ex), exc_info=True)
                    self._put_value_in_result_queue(ex)
        logger.debug(
            "(%s) runner connection closed", self.study_id)
        self.close()
        logger.debug(
            "(%s) connection pool status %s", self.study_id,
            self.connection_pool.status()
        )
        self._finalize(started)

    def _wait_cursor_executing(
        self, cursor: impala.hiveserver2.HiveServer2Cursor
    ) -> None:
        while True:
            if self.is_closed():
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

    def _finalize(self, started: float) -> None:
        logger.debug("(%s) going to finalize", self.study_id)
        with self._status_lock:
            self._done = True
        elapsed = time.time() - started
        logger.debug("(%s) runner done in %0.3f sec", self.study_id, elapsed)
        logger.debug(
            "(%s) connection pool status: %s", self.study_id,
            self.connection_pool.status())
        logger.info("(%s) returned %s rows", self.study_id, self._counter)
