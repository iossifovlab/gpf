# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
from typing import Any, cast

import pytest
import pytest_mock

from dae.genomic_resources.cli import cli_manage
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
from dae.genomic_resources.repository import (
    GenomicResource,
    GenomicResourceRepo,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.genomic_resources.testing import (
    convert_to_tab_separated,
    setup_directories,
)
from dae.task_graph.executor import SequentialExecutor, task_graph_run
from dae.task_graph.graph import TaskGraph


@pytest.fixture
def test_grr(tmp_path: pathlib.Path) -> GenomicResourceRepo:
    root_path = tmp_path
    setup_directories(
        root_path, {
            "grr.yaml": textwrap.dedent(f"""
                id: reannotation_repo
                type: dir
                directory: "{root_path}/grr"
            """),
            "grr": {
                "score_one": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        type: cnv_collection
                        table:
                            filename: data.txt
                        scores:
                            - id: freq
                              name: frequency
                              type: float
                              histogram:
                                type: number
                                number_of_bins: 3
                                view_range:
                                  min: 0
                                  max: 1
                                x_log_scale: false
                                y_log_scale: true
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
                    """),
                    "data.txt": convert_to_tab_separated(textwrap.dedent("""
                chrom  pos_begin  pos_end  frequency  collection affected_status
                1      10         20       0.02       SSC        affected
                1      50         100      0.1        SSC        affected
                2      1          8        0.00001    AGRE       unaffected
                2      16         20       0.3        SSC        affected
                2      200        203      0.0002     AGRE       unaffected
                15     16         20       0.2        AGRE       affected
                    """)),
                },
            },
        },
    )
    return build_genomic_resource_repository(file_name=str(
        root_path / "grr.yaml",
    ))


@pytest.fixture
def cnvs(test_grr: GenomicResourceRepo) -> CnvCollection:
    return CnvCollection(test_grr.get_resource("score_one"))


@pytest.fixture
def cnvs_resource(test_grr: GenomicResourceRepo) -> GenomicResource:
    return test_grr.get_resource("score_one")


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
    with pytest.raises(
        ValueError,
        match="The resource <score_one> is not open",
    ):
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
    tmp_path: pathlib.Path,
    test_grr: GenomicResourceRepo,  # noqa: ARG001
) -> None:
    grr_path = tmp_path / "grr"
    assert not (grr_path / "/score_one/statistics").exists()

    cli_manage([
        "resource-repair",
        "-R", str(grr_path),
        "-r", "score_one",
        "-j", "1",
    ])

    assert (grr_path / "score_one/statistics").exists()

    assert (grr_path / "score_one/statistics/histogram_freq.json").exists()
    hist_file = (
        grr_path / "score_one/statistics/histogram_freq.json"
    ).read_text().replace(" ", "").replace("\n", "")
    assert hist_file.find('"bars":[6,0,0]') != -1
