
import time

from concurrent.futures import ThreadPoolExecutor
from queue import Queue

from dae.backends.query_runners import QueryResult

from dae.backends.impala.impala_variants import ImpalaQueryRunner


def create_runner(impala_helpers, query, deserializer=None):

    connection = impala_helpers.connection()
    runner = ImpalaQueryRunner(
        connection, query, deserializer=deserializer)
    return runner


def test_impala_runner_simple(impala_helpers):
    assert impala_helpers is not None

    query = "SELECT * FROM gpf_variant_db.test_study_impala_01_variants"
    result_queue = Queue(maxsize=3)

    runner = create_runner(impala_helpers, query)
    runner._set_result_queue(result_queue)
    assert not runner.started()

    executor = ThreadPoolExecutor(max_workers=1)
    runner.start(executor)
    time.sleep(1)

    assert runner.started()

    runner.close()
    time.sleep(1)

    assert runner.closed()
    assert runner.done()

    executor.shutdown(wait=True)


def test_impala_runner_result_simple(impala_helpers):
    query = "SELECT * FROM gpf_variant_db.test_study_impala_01_variants"
    result_queue = Queue(maxsize=3)

    runner = create_runner(impala_helpers, query)
    assert not runner.started()

    executor = ThreadPoolExecutor(max_workers=1)
    result = QueryResult(result_queue, [runner])
    result.start(executor)
    time.sleep(0.1)

    assert runner.started()

    for row in result:
        print(row)
        break

    result.close()
    time.sleep(0.5)

    assert runner.closed()

    executor.shutdown(wait=True)


def test_impala_runner_result_experimental_1(impala_helpers):
    query = "SELECT COUNT(" \
        "DISTINCT bucket_index, " \
        "summary_variant_index, " \
        "family_variant_index) " \
        "FROM gpf_variant_db.test_study_impala_01_variants"
    result_queue = Queue(maxsize=3)

    runner = create_runner(impala_helpers, query)
    assert not runner.started()

    executor = ThreadPoolExecutor(max_workers=1)
    result = QueryResult(result_queue, [runner])
    result.start(executor)

    for row in result:
        print(row)
        time.sleep(0.5)

    result.close()
    executor.shutdown(wait=True)


def test_impala_runner_result_experimental_2(impala_helpers):
    query = "SELECT COUNT(" \
        "DISTINCT bucket_index, " \
        "summary_variant_index, " \
        "family_variant_index) " \
        "FROM gpf_variant_db.test_study_impala_01_variants"
    result_queue = Queue(maxsize=3)

    runner = create_runner(impala_helpers, query)
    assert not runner.started()

    executor = ThreadPoolExecutor(max_workers=1)
    result = QueryResult(result_queue, [runner])
    result.start(executor)
    time.sleep(0.1)

    assert runner.started()

    result.close()
    time.sleep(0.1)
    executor.shutdown(wait=True)


def test_impala_runner_result_experimental(impala_helpers):
    query = "SELECT COUNT(" \
        "DISTINCT bucket_index, " \
        "summary_variant_index, " \
        "family_variant_index) " \
        "FROM gpf_variant_db.test_study_impala_01_variants"
    result_queue = Queue(maxsize=3)

    runner = create_runner(impala_helpers, query)

    assert not runner.started()

    executor = ThreadPoolExecutor(max_workers=1)
    result = QueryResult(result_queue, [runner])
    result.start(executor)
    time.sleep(0.1)

    assert runner.started()

    for row in result:
        print(row)
        break

    result.close()
    time.sleep(0.5)

    assert runner.closed()
    executor.shutdown(wait=True)
