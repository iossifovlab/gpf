from dae.backends.impala.impala_helpers import ImpalaQueryResult
import time

from queue import Queue


def test_impala_runner_simple(impala_helpers):
    assert impala_helpers is not None

    query = "SELECT * FROM gpf_variant_db.test_study_impala_01_variants"
    result_queue = Queue(maxsize=3)

    runner = impala_helpers._submit(query)
    runner._set_result_queue(result_queue)
    assert not runner.started()

    runner.start()
    time.sleep(1)

    assert runner.started()

    runner.close()
    time.sleep(1)

    assert runner.done()


def test_impala_runner_result_simple(impala_helpers):
    query = "SELECT * FROM gpf_variant_db.test_study_impala_01_variants"
    result_queue = Queue(maxsize=3)

    runner = impala_helpers._submit(query)
    assert not runner.started()

    result = ImpalaQueryResult(result_queue, [runner])
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

    runner = impala_helpers._submit(query)
    assert not runner.started()

    result = ImpalaQueryResult(result_queue, [runner])
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

    runner = impala_helpers._submit(query)
    assert not runner.started()

    result = ImpalaQueryResult(result_queue, [runner])
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

    runner = impala_helpers._submit(query)

    assert not runner.started()

    result = ImpalaQueryResult(result_queue, [runner])
    result.start()
    time.sleep(0.1)

    assert runner.started()

    for row in result:
        print(row)
        break

    result.close()
    time.sleep(0.5)

    assert runner.closed()


