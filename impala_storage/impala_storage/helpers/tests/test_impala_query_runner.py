# pylint: disable=W0621,C0114,C0116,W0212,W0613
import time

from concurrent.futures import ThreadPoolExecutor
from queue import Queue

import pytest

from dae.query_variants.query_runners import QueryResult

from dae.impala_storage.helpers.impala_query_runner import ImpalaQueryRunner


@pytest.fixture(scope="session")
def impala_helpers(impala_genotype_storage):
    return impala_genotype_storage.impala_helpers


def create_runner(impala_helpers, query, deserializer=None):

    runner = ImpalaQueryRunner(
        impala_helpers._connection_pool, query, deserializer=deserializer)
    return runner


def test_impala_runner_simple(impala_helpers):
    assert impala_helpers is not None

    query = "SELECT * FROM gpf_variant_db.test_study_impala_01_variants"
    result_queue: Queue = Queue(maxsize=3)

    runner = create_runner(impala_helpers, query)
    runner._set_result_queue(result_queue)
    assert not runner.started()

    executor = ThreadPoolExecutor(max_workers=1)
    runner.start(executor)
    time.sleep(1)

    assert runner.started()

    runner.close()
    time.sleep(1)

    assert runner.is_closed()
    assert runner.is_done()

    executor.shutdown(wait=True)


def test_impala_runner_result_with_exception(impala_helpers):
    query = "SELECT * FROM gpf_variant_db.test_study_impala_01_variants"

    runner = create_runner(impala_helpers, query)
    assert not runner.started()

    result = QueryResult([runner])
    result.start()
    time.sleep(0.1)

    assert runner.started()

    for row in result:
        print(row)
        break

    with pytest.raises(
            IOError,
            match="AnalysisException: Could not resolve table reference:"):
        result.close()
    time.sleep(0.5)

    assert runner.is_closed()


def test_impala_runner_result_experimental_1(impala_helpers):
    query = "SELECT COUNT(" \
        "DISTINCT bucket_index, " \
        "summary_variant_index, " \
        "family_variant_index) " \
        "FROM gpf_variant_db.test_study_impala_01_variants"

    runner = create_runner(impala_helpers, query)
    assert not runner.started()

    result = QueryResult([runner])
    result.start()

    for row in result:
        print(row)
        time.sleep(0.5)

    with pytest.raises(
            IOError,
            match="AnalysisException: Could not resolve table reference:"):
        result.close()


def test_impala_runner_result_experimental_2(impala_helpers):
    query = "SELECT COUNT(" \
        "DISTINCT bucket_index, " \
        "summary_variant_index, " \
        "family_variant_index) " \
        "FROM gpf_variant_db.test_study_impala_01_variants"

    runner = create_runner(impala_helpers, query)
    assert not runner.started()

    result = QueryResult([runner])
    result.start()
    time.sleep(0.1)

    assert runner.started()

    with pytest.raises(
            IOError,
            match="AnalysisException: Could not resolve table reference:"):
        result.close()
    time.sleep(0.1)


def test_impala_runner_result_experimental(impala_helpers):
    query = "SELECT COUNT(" \
        "DISTINCT bucket_index, " \
        "summary_variant_index, " \
        "family_variant_index) " \
        "FROM gpf_variant_db.test_study_impala_01_variants"

    runner = create_runner(impala_helpers, query)

    assert not runner.started()

    result = QueryResult([runner])
    result.start()
    time.sleep(0.1)

    assert runner.started()

    for row in result:
        print(row)
        break

    with pytest.raises(
            IOError,
            match="AnalysisException: Could not resolve table reference:"):
        result.close()
    time.sleep(0.5)

    assert runner.is_closed()
