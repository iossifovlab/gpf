import time
import queue
import logging
from dae.query_variants.query_runners import QueryRunner

logger = logging.getLogger(__name__)


class BigQueryQueryRunner(QueryRunner):
    """Run a Impala query in a separate thread."""

    def __init__(self, connection_factory, query, deserializer=None):
        super().__init__(deserializer=deserializer)

        self.client = connection_factory
        self.query = query

    def run(self):
        """Execute the query and enqueue the resulting rows."""
        started = time.time()
        logger.debug(
            "bigquery runner (%s) started", self.study_id)

        try:
            if self.closed():
                logger.info(
                    "runner (%s) closed before execution",
                    self.study_id)
                self._finalize(started)
                return

            for record in self.client.query(self.query):
                val = self.deserializer(record)
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

    def _put_value_in_result_queue(self, val):
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

    def _finalize(self, started):
        with self._status_lock:
            self._done = True
        elapsed = time.time() - started
        logger.debug("runner (%s) done in %0.3f sec", self.study_id, elapsed)
