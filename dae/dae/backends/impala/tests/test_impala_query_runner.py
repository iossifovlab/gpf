from dae.backends.query_runners import QueryResult
import time

from dae.backends.impala.impala_variants import ImpalaQueryRunner

from queue import Queue


def submit(impala_helpers, query, deserializer=None):

    connection = impala_helpers.connection()
    runner = ImpalaQueryRunner(
        connection, query, deserializer=deserializer)
    runner._owner = impala_helpers
    return runner


def test_impala_runner_simple(impala_helpers):
    assert impala_helpers is not None

    query = "SELECT * FROM gpf_variant_db.test_study_impala_01_variants"
    result_queue = Queue(maxsize=3)

    runner = submit(impala_helpers, query)
    runner._set_result_queue(result_queue)
    assert not runner.started()

    runner.start()
    time.sleep(1)

    assert runner.started()

    runner.close()
    time.sleep(1)

    assert runner.closed()
    assert runner.done()


def test_impala_runner_result_simple(impala_helpers):
    query = "SELECT * FROM gpf_variant_db.test_study_impala_01_variants"
    result_queue = Queue(maxsize=3)

    runner = submit(impala_helpers, query)
    assert not runner.started()

    result = QueryResult(result_queue, [runner])
    result.start()
    time.sleep(0.1)

    assert runner.started()

    for row in result:
        print(row)
        break

    result.close()
    time.sleep(0.5)

    assert runner.closed()


def test_impala_runner_result_experimental_1(impala_helpers):
    query = "SELECT COUNT(" \
        "DISTINCT bucket_index, " \
        "summary_variant_index, " \
        "family_variant_index) " \
        "FROM gpf_variant_db.test_study_impala_01_variants"
    result_queue = Queue(maxsize=3)

    runner = submit(impala_helpers, query)
    assert not runner.started()

    result = QueryResult(result_queue, [runner])
    result.start()

    for row in result:
        print(row)
        time.sleep(0.5)

    result.close()


def test_impala_runner_result_experimental_2(impala_helpers):
    query = "SELECT COUNT(" \
        "DISTINCT bucket_index, " \
        "summary_variant_index, " \
        "family_variant_index) " \
        "FROM gpf_variant_db.test_study_impala_01_variants"
    result_queue = Queue(maxsize=3)

    runner = submit(impala_helpers, query)
    assert not runner.started()

    result = QueryResult(result_queue, [runner])
    result.start()
    time.sleep(0.1)

    assert runner.started()

    result.close()
    time.sleep(0.1)


def test_impala_runner_result_experimental(impala_helpers):
    query = "SELECT COUNT(" \
        "DISTINCT bucket_index, " \
        "summary_variant_index, " \
        "family_variant_index) " \
        "FROM gpf_variant_db.test_study_impala_01_variants"
    result_queue = Queue(maxsize=3)

    runner = submit(impala_helpers, query)

    assert not runner.started()

    result = QueryResult(result_queue, [runner])
    result.start()
    time.sleep(0.1)

    assert runner.started()

    for row in result:
        print(row)
        break

    result.close()
    time.sleep(0.5)

    assert runner.closed()


