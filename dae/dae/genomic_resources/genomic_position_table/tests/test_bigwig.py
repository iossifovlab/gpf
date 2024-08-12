# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import pathlib
import textwrap

import pytest
import pytest_mock

from dae.genomic_resources.genomic_position_table.table_bigwig import (
    BigWigTable,
)
from dae.genomic_resources.genomic_position_table.utils import (
    build_genomic_position_table,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    setup_bigwig,
    setup_directories,
)


@pytest.fixture(scope="module")
def test_grr(tmp_path_factory: pytest.TempPathFactory) -> GenomicResourceRepo:
    root_path = tmp_path_factory.mktemp("bigwig_testdir")
    setup_directories(
        root_path,
        {
            "grr.yaml": textwrap.dedent(f"""
                id: test_grr
                type: directory
                directory: {root_path!s}
            """),
            "test_score": {
                "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.bw
                        scores:
                        - id: score_one
                          type: float
                          index: 3
                """),
            },
        },
    )
    data = textwrap.dedent("""
        chr1   0          10       0.01
        chr1   10         20       0.02
        chr1   20         30       0.03
        chr2   30         40       0.04
        chr2   40         50       0.05
        chr2   50         70       0.06
        chr3   70         80       0.07
        chr3   80         90       0.08
        chr3   90         120      0.09
    """)
    setup_bigwig(
        root_path / "test_score" / "data.bw", data,
        {"chr1": 1000,
         "chr2": 2000,
         "chr3": 3000},
    )
    return build_filesystem_test_repository(root_path)


@pytest.fixture(scope="module")
def bigwig_table(test_grr: GenomicResourceRepo) -> BigWigTable:
    table = BigWigTable(
        test_grr.get_resource("test_score"),
        {"filename": "data.bw", "format": "bigWig"},
    )
    assert table is not None
    return table


def test_get_chromosomes(bigwig_table: BigWigTable) -> None:
    with bigwig_table:
        assert bigwig_table.get_chromosomes() == ["chr1", "chr2", "chr3"]


def test_get_chromosome_length(bigwig_table: BigWigTable) -> None:
    with bigwig_table:
        assert bigwig_table.get_chromosome_length("chr1") == 1000
        assert bigwig_table.get_chromosome_length("chr2") == 2000
        assert bigwig_table.get_chromosome_length("chr3") == 3000


def test_get_chromosome_length_missing(bigwig_table: BigWigTable) -> None:
    with bigwig_table, pytest.raises(
            ValueError,
            match="contig chrX not present in the table's contigs"):
        bigwig_table.get_chromosome_length("chrX")


def test_get_all_records(bigwig_table: BigWigTable) -> None:
    with bigwig_table:
        vs = list(bigwig_table.get_all_records())
        assert len(vs) == 9
        line = vs[0]
        assert line.chrom == "chr1"
        assert line.pos_begin == 1
        assert line.pos_end == 10
        assert line.get(3) == pytest.approx(0.01)


def test_get_records_in_region(bigwig_table: BigWigTable) -> None:
    with bigwig_table:
        vs = list(bigwig_table.get_records_in_region("chr1"))
        assert len(vs) == 3


def test_get_records_in_region_with_position(bigwig_table: BigWigTable) -> None:
    with bigwig_table:
        vs = list(bigwig_table.get_records_in_region("chr1", 1, 9))
        assert len(vs) == 1


def test_get_records_begin_pos_out_of_bounds(bigwig_table: BigWigTable) -> None:
    with bigwig_table:
        vs = list(bigwig_table.get_records_in_region("chr1", -1))
        assert len(vs) == 3


def test_get_records_end_pos_out_of_bounds(bigwig_table: BigWigTable) -> None:
    with bigwig_table:
        vs = list(bigwig_table.get_records_in_region("chr1", 1, 999_999_999))
        assert len(vs) == 3


def test_get_records_in_region_with_position_single(
    bigwig_table: BigWigTable,
) -> None:
    with bigwig_table:
        vs = list(bigwig_table.get_records_in_region("chr1", 5, 5))
        assert len(vs) == 1


def test_get_records_in_region_left_only(bigwig_table: BigWigTable) -> None:
    with bigwig_table:
        vs = list(bigwig_table.get_records_in_region("chr1", pos_begin=21))
        assert len(vs) == 1


def test_get_records_in_region_right_only(bigwig_table: BigWigTable) -> None:
    with bigwig_table:
        vs = list(bigwig_table.get_records_in_region("chr1", pos_end=20))
        assert len(vs) == 2


def test_get_records_in_region_missing_chrom(bigwig_table: BigWigTable) -> None:
    with bigwig_table, pytest.raises(KeyError):
        list(bigwig_table.get_records_in_region("chrX"))


def test_build_genomic_position_table_bigwig(
    test_grr: GenomicResourceRepo,
) -> None:
    res = test_grr.get_resource("test_score")

    table = build_genomic_position_table(
        res, {"filename": "data.bw", "format": "bigWig"},
    )
    assert isinstance(table, BigWigTable)

    table = build_genomic_position_table(
        res, {"filename": "data.bw"},
    )
    assert isinstance(table, BigWigTable)


def test_bigwig_genomic_position_table_chrom_mapping_works(
    tmp_path: pathlib.Path,
) -> None:
    root_path = tmp_path
    setup_directories(
        root_path,
        {
            "grr.yaml": textwrap.dedent(f"""
                id: test_grr
                type: directory
                directory: {root_path!s}
            """),
            "test_score": {
                "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.bw
                            chrom_mapping:
                                del_prefix: chr
                        scores:
                        - id: score_one
                          type: float
                          index: 3
                """),
            },
        },
    )
    data = textwrap.dedent("""
        chr1   0          10       0.01
        chr2   10         20       0.02
        chr3   20         30       0.03
    """)
    setup_bigwig(
        root_path / "test_score" / "data.bw", data,
        {"chr1": 1000,
         "chr2": 2000,
         "chr3": 3000},
    )
    grr = build_filesystem_test_repository(root_path)
    assert grr is not None
    res = grr.get_resource("test_score")
    with BigWigTable(res, res.get_config()["table"]) as bigwig_table:
        assert bigwig_table.get_chromosomes() == ["1", "2", "3"]
        vs = list(bigwig_table.get_all_records())
        assert len(vs) == 3
        assert vs[0].chrom == "1"
        assert vs[1].chrom == "2"
        assert vs[2].chrom == "3"

        vs = list(bigwig_table.get_records_in_region("1"))
        assert len(vs) == 1
        assert vs[0].chrom == "1"


def test_bigwig_correct_fetching_of_intervals(
    tmp_path: pathlib.Path,
) -> None:
    # Make sure there are no duplicated entries returned:
    # This was happening with naive incrementation of the start/stop fetch
    # positions, as it was possible to land in the middle of a long entry
    # spanning many bases, which would be returned more than once by the
    # intervals fetching method

    root_path = tmp_path
    setup_directories(
        root_path,
        {
            "grr.yaml": textwrap.dedent(f"""
                id: test_grr
                type: directory
                directory: {root_path!s}
            """),
            "test_score": {
                "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.bw
                            format: bigWig
                        scores:
                        - id: score_one
                          type: float
                          index: 3
                """),
            },
        },
    )
    data = textwrap.dedent("""
        chr1   0          10000       0.01
        chr1   10000      20000       0.02
        chr1   20000      30000       0.03
        chr1   30000      40000       0.04
        chr1   40000      50000       0.05
        chr1   50000      60000       0.06
    """)
    setup_bigwig(
        root_path / "test_score" / "data.bw", data,
        {"chr1": 100_000},
    )
    grr = build_filesystem_test_repository(root_path)
    assert grr is not None
    res = grr.get_resource("test_score")
    table_definition = res.get_config()["table"]
    with BigWigTable(res, table_definition) as bigwig_table:
        vs = list(bigwig_table.get_all_records())
        assert len(vs) == 6
        vs = list(bigwig_table.get_records_in_region("chr1", 1))
        assert len(vs) == 6
        vs = list(bigwig_table.get_records_in_region("chr1", 0, 30000))
        assert len(vs) == 3


def test_no_repeating_in_buffered(
    tmp_path: pathlib.Path,
) -> None:
    root_path = tmp_path
    setup_directories(
        root_path,
        {
            "grr.yaml": textwrap.dedent(f"""
                id: test_grr
                type: directory
                directory: {root_path!s}
            """),
            "test_score": {
                "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.bw
                            format: bigWig
                        scores:
                        - id: score_one
                          type: float
                          index: 3
                """),
            },
        },
    )
    data = textwrap.dedent("""
        chr1   0         1000       0.01
        chr1   1000      1001       0.02
        chr1   1001      1002       0.03
        chr1   1002      1003       0.04
        chr1   1003      1004       0.05
    """)
    setup_bigwig(
        root_path / "test_score" / "data.bw", data,
        {"chr1": 5000},
    )
    grr = build_filesystem_test_repository(root_path)
    assert grr is not None
    res = grr.get_resource("test_score")
    table_definition = res.get_config()["table"]
    with BigWigTable(res, table_definition) as bigwig_table:
        vs = list(bigwig_table.get_records_in_region("chr1", 1001, 1001))
        assert len(vs) == 1
        assert vs[0].chrom == "chr1"
        assert vs[0].pos_begin == 1001
        assert vs[0].pos_end == 1001
        vs = list(bigwig_table.get_records_in_region("chr1", 1002, 1002))
        assert len(vs) == 1
        assert vs[0].chrom == "chr1"
        assert vs[0].pos_begin == 1002
        assert vs[0].pos_end == 1002
        vs = list(bigwig_table.get_records_in_region("chr1", 1003, 1003))
        assert len(vs) == 1
        assert vs[0].chrom == "chr1"
        assert vs[0].pos_begin == 1003
        assert vs[0].pos_end == 1003


def test_bigwig_buffering_switching(
    tmp_path: pathlib.Path, mocker: pytest_mock.MockerFixture,
) -> None:
    root_path = tmp_path
    setup_directories(
        root_path,
        {
            "grr.yaml": textwrap.dedent(f"""
                id: test_grr
                type: directory
                directory: {root_path!s}
            """),
            "test_score": {
                "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.bw
                            format: bigWig
                        scores:
                        - id: score_one
                          type: float
                          index: 3
                """),
            },
        },
    )
    data = textwrap.dedent("""
        chr1   0        100       0.01
        chr1   100      500       0.02
        chr1   500      1500      0.03
    """)
    setup_bigwig(
        root_path / "test_score" / "data.bw", data,
        {"chr1": 100_000},
    )
    grr = build_filesystem_test_repository(root_path)
    assert grr is not None
    res = grr.get_resource("test_score")
    table_definition = res.get_config()["table"]

    mocker.spy(BigWigTable, "_fetch_direct")
    mocker.spy(BigWigTable, "_fetch_buffered")

    with BigWigTable(res, table_definition) as bigwig_table:
        assert BigWigTable._fetch_direct.call_count   == 0  # type: ignore
        assert BigWigTable._fetch_buffered.call_count == 0  # type: ignore

        list(bigwig_table.get_records_in_region("chr1", 0, 200))
        assert BigWigTable._fetch_direct.call_count   == 1  # type: ignore
        assert BigWigTable._fetch_buffered.call_count == 0  # type: ignore

        list(bigwig_table.get_records_in_region("chr1", 200, 500))
        assert BigWigTable._fetch_direct.call_count   == 1  # type: ignore
        assert BigWigTable._fetch_buffered.call_count == 1  # type: ignore

        list(bigwig_table.get_records_in_region("chr1", 1000, 1000))
        assert BigWigTable._fetch_direct.call_count   == 2  # type: ignore
        assert BigWigTable._fetch_buffered.call_count == 1  # type: ignore
