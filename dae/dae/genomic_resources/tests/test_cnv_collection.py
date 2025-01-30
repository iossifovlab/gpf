# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
from typing import Any, cast

import pytest
import pytest_mock

from dae.genomic_resources.cli import cli_manage
from dae.genomic_resources.fsspec_protocol import FsspecReadWriteProtocol
from dae.genomic_resources.genomic_scores import (
    CnvCollection,
)
from dae.genomic_resources.histogram import (
    HistogramConfig,
    NumberHistogram,
    build_histogram_config,
)
from dae.genomic_resources.implementations.genomic_scores_impl import (
    CnvCollectionImplementation,
)
from dae.genomic_resources.repository import GR_CONF_FILE_NAME, GenomicResource
from dae.genomic_resources.testing import (
    build_filesystem_test_protocol,
    build_inmemory_test_resource,
    setup_directories,
    setup_tabix,
)
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
def proto_fixture(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[pathlib.Path, FsspecReadWriteProtocol]:
    path = tmp_path_factory.mktemp("cli_info_repo_fixture")
    setup_directories(
        path,
        {
            "one": {
                GR_CONF_FILE_NAME: textwrap.dedent("""
                    type: cnv_collection
                    table:
                        filename: data.txt.gz
                        format: tabix
                    scores:
                        - id: phastCons100way
                          type: float
                          name: s1
                          histogram:
                            type: number
                            number_of_bins: 5
                    """),
            },
        })
    setup_tabix(
        path / "one" / "data.txt.gz",
        """
        #chrom  pos_begin  pos_end  s1    s2    frequency
        1       10         20       0.2   1.2   1
        1       30         50       0.3   1.3   2
        1       100        120      0.4   1.4   3
        2       10         50       0.1   2.1   4
        2       70         200      0.2   2.2   2
        """, seq_col=0, start_col=1, end_col=2)
    proto = build_filesystem_test_protocol(path)
    return path, proto


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


def test_cnv_collection_implementation_histogram(
    cnvs_resource: GenomicResource,
) -> None:
    hist_conf = build_histogram_config({
        "histogram": {
            "type": "number",
            "view_range": {"min": 0, "max": 0.3},
            "number_of_bins": 2,
        },
    })
    assert isinstance(hist_conf, HistogramConfig)

    hist_confs = {"freq": hist_conf}

    histograms = CnvCollectionImplementation._do_histogram(
        cnvs_resource, hist_confs, "2", 0, 300,
    )

    assert isinstance(histograms["freq"], NumberHistogram)
    assert histograms["freq"].min_value == 1e-05
    assert histograms["freq"].max_value == 0.3
    assert histograms["freq"].bars.tolist() == [2, 1]
    assert histograms["freq"].bins.tolist() == [0, 0.15, 0.3]


def test_cli_manage_cnv_collection_histograms(
     proto_fixture: tuple[pathlib.Path, FsspecReadWriteProtocol],
) -> None:
    path, _proto = proto_fixture
    assert not (path / "one/index.html").exists()

    cli_manage(["resource-repair", "-R", str(path), "-r", "one", "-j", "1"])

    assert (path / "one/statistics").exists()

    hist_file = (
        path / "one/statistics/histogram_phastCons100way.json"
    ).read_text().replace(" ", "").replace("\n", "")

    assert hist_file.find('"bars":[1,2,0,1,1]') != -1
