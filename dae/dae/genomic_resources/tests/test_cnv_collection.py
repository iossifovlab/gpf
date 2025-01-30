# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any, cast

import pytest
import pytest_mock

from dae.genomic_resources.genomic_scores import (
    CnvCollection,
)
from dae.genomic_resources.implementations.genomic_scores_impl import (
    CnvCollectionImplementation,
)
from dae.genomic_resources.repository import GR_CONF_FILE_NAME, GenomicResource
from dae.genomic_resources.testing import build_inmemory_test_resource
from dae.task_graph.executor import SequentialExecutor, task_graph_run
from dae.task_graph.graph import TaskGraph


@pytest.fixture
def cnvs_resource() -> GenomicResource:
    res = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: cnv_collection
            table:
                filename: data.mem
            scores:
                - id: freq
                  name: frequency
                  type: float
                  desc: some populaton frequency
                - id: collection
                  name: collection
                  type: str
                  desc: SSC or AGRE
                - id: status
                  name: affected_status
                  type: str
                  desc: |
                    shows if the child that has the de novo
                    is affected or unaffected
        """,
        "data.mem": """
            chrom  pos_begin  pos_end  frequency  collection affected_status
            1      10         20       0.02       SSC        affected
            1      50         100      0.1        SSC        affected
            2      1          8        0.00001    AGRE       unaffected
            2      16         20       0.3        SSC        affected
            2      200        203      0.0002     AGRE       unaffected
            15     16         20       0.2        AGRE       affected
        """,
    })
    assert res.get_type() == "cnv_collection"
    return res


@pytest.fixture
def cnvs(cnvs_resource: GenomicResource) -> CnvCollection:
    return CnvCollection(cnvs_resource)


@pytest.mark.parametrize("chrom,beg,end,count,attributes", [
    ("1", 5, 15, 1, [
        {"freq": 0.02, "collection": "SSC", "status": "affected"},
    ]),
    ("1", 60, 70, 1, [
        {"freq": 0.1, "collection": "SSC", "status": "affected"},
    ]),
    ("1", 10, 65, 2, [
        {"freq": 0.02, "collection": "SSC", "status": "affected"},
        {"freq": 0.1, "collection": "SSC", "status": "affected"},
    ]),
    ("2", 5, 15, 1, [
        {"freq": 0.00001, "collection": "AGRE", "status": "unaffected"},
    ]),
    ("2", 15, 25, 1, [
        {"freq": 0.3, "collection": "SSC", "status": "affected"},
    ]),
    ("2", 8, 25, 2, [
        {"freq": 0.00001, "collection": "AGRE", "status": "unaffected"},
        {"freq": 0.3, "collection": "SSC", "status": "affected"},
    ]),
])
def test_cnv_collection_resource(
    cnvs: CnvCollection,
    chrom: str,
    beg: int,
    end: int,
    count: int,
    attributes: dict[str, Any],
) -> None:
    with cnvs.open() as cnv_collection:
        aaa = cast(CnvCollection, cnv_collection).fetch_cnvs(
            chrom, beg, end)
        assert len(aaa) == count
        assert [a.attributes for a in aaa] == attributes


def test_cnv_collection_wrong_resource_types(
    cnvs_resource: GenomicResource,
    mocker: pytest_mock.MockFixture,
) -> None:
    mocker.patch.object(
        cnvs_resource,
        "get_type",
        return_value="aaaa")

    with pytest.raises(
            ValueError,
            match="The resource provided to CnvCollection should be of "
            "'cnv_collection' type, not a 'aaaa'"):
        CnvCollection(cnvs_resource)


def test_cnv_collection_no_open(cnvs: CnvCollection) -> None:
    with pytest.raises(ValueError, match="The resource <> is not open"):
        cnvs.fetch_cnvs("1", 5, 15)


def test_cnv_collection_bad_chrom(cnvs: CnvCollection) -> None:
    cnv_collection = cast(CnvCollection, cnvs.open())
    res = cnv_collection.fetch_cnvs("3", 5, 15)

    assert len(res) == 0


@pytest.fixture
def cnvs_impl(cnvs_resource: GenomicResource) -> CnvCollectionImplementation:

    return CnvCollectionImplementation(cnvs_resource)


def test_cnv_collection_implementation(
    cnvs_impl: CnvCollectionImplementation,
) -> None:
    assert cnvs_impl is not None
    task_graph = TaskGraph()
    tasks = cnvs_impl.add_statistics_build_tasks(task_graph)
    assert len(tasks) == 1
    executor = SequentialExecutor()
    task_graph_run(task_graph, executor)

    res_hash = cnvs_impl.calc_info_hash()
    assert res_hash == b"infohash"

    res_hash = cnvs_impl.calc_statistics_hash()
    assert b"affected_status" in res_hash

    info = cnvs_impl.get_info()
    assert "some populaton frequency" in info

    info = cnvs_impl.get_statistics_info()
    assert "Filename" in info
