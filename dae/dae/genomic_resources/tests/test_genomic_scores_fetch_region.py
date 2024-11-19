# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
from typing import cast

import pytest

from dae.genomic_resources.genomic_scores import (
    AlleleScore,
    NPScore,
    PositionScore,
    ScoreValue,
    build_score_from_resource,
)
from dae.genomic_resources.testing import (
    build_filesystem_test_resource,
    setup_directories,
    setup_tabix,
)


@pytest.fixture(scope="module")
def position_score(tmp_path_factory: pytest.TempPathFactory) -> PositionScore:
    root_path = tmp_path_factory.mktemp("position_score")
    setup_directories(
        root_path, {
            "genomic_resource.yaml": """
                type: position_score
                table:
                  filename: data.txt.gz
                  format: tabix
                  header_mode: none
                  chrom:
                    index: 0
                  pos_begin:
                    index: 1
                  pos_end:
                    index: 2
                scores:
                - id: s1
                  index: 3
                  type: float
                - id: s2
                  index: 4
                  type: float
            """,
        })
    setup_tabix(
        root_path / "data.txt.gz",
        textwrap.dedent("""
        chr1     11        13       1.0    10.0
        chr1     21        23       2.0    na
        chr1     31        33       3.0    30.0
        chr1     41        43       na     40.0
        chr1     51        53       na     na

        chr2     61        73       6.0    60.0
        chr2     71        73       7.0    70.0

        chr3     61        73       6.0    60.0
        chr3     73        73       7.0    70.0
        """).strip(),
        seq_col=0, start_col=1, end_col=2)
    res = build_filesystem_test_resource(root_path)
    score = build_score_from_resource(res)
    score.open()
    assert len(score.score_definitions) == 2
    assert "s1" in score.score_definitions
    assert "s2" in score.score_definitions
    return cast(PositionScore, score)


@pytest.mark.parametrize("begin,end,scores,expected", [
    (1, 10, None, []),
    (10, 20, ["s1"], [(11, 13, [1.0])]),
    (20, 30, ["s1"], [(21, 23, [2.0])]),
    (30, 40, ["s1"], [(31, 33, [3.0])]),
    (10, 20, ["s2"], [(11, 13, [10.0])]),
    (20, 30, ["s2"], [(21, 23, [None])]),
    (30, 40, ["s2"], [(31, 33, [30.0])]),
    (40, 60, ["s1"], [(41, 43, [None]), (51, 53, [None])]),
    (40, 60, ["s1", "s2"],
     [(41, 43, [None, 40.0]), (51, 53, [None, None])]),
    (40, 60, None,
     [(41, 43, [None, 40.0]), (51, 53, [None, None])]),
    (40, 60, ["s2", "s1"],
     [(41, 43, [40.0, None]), (51, 53, [None, None])]),
    (30, 40, None, [(31, 33, [3.0, 30.0])]),
    (10, 30, None, [(11, 13, [1.0, 10.0]), (21, 23, [2.0, None])]),
    (20, 40, None, [(21, 23, [2.0, None]), (31, 33, [3.0, 30.0])]),
])
def test_position_score_fetch_region(
    position_score: PositionScore,
    begin: int | None,
    end: int | None,
    scores: list[str] | None,
    expected: list[tuple[int, int, list[ScoreValue]]],
) -> None:

    score_lines = list(
        position_score.fetch_region("chr1", begin, end, scores=scores))

    assert len(score_lines) == len(expected)
    assert score_lines == expected


@pytest.mark.parametrize("chrom,begin,end", [
    ("chr2", 60, 120),
    ("chr3", 60, 120),
])
def test_position_score_fetch_region_consistency(
    position_score: PositionScore,
    chrom: str,
    begin: int | None,
    end: int | None,
) -> None:

    with pytest.raises(ValueError, match="multiple values for positions"):
        list(position_score.fetch_region(chrom, begin, end))


@pytest.fixture(scope="module")
def np_score(tmp_path_factory: pytest.TempPathFactory) -> NPScore:
    root_path = tmp_path_factory.mktemp("np_score")
    setup_directories(
        root_path, {
        "genomic_resource.yaml": """
            type: np_score
            table:
                filename: data.txt.gz
                format: tabix
                reference:
                  name: ref
                alternative:
                  name: alt
            scores:
                - id: s1
                  type: float
                  name: s1

                - id: s2
                  type: float
                  name: s2
        """,
    })
    setup_tabix(
        root_path / "data.txt.gz",
        textwrap.dedent("""
            #chrom  pos_begin  pos_end  ref  alt  s1    s2
            chr1   1           3        A    G    0.1   1.0
            chr1   1           3        A    C    0.1   1.0
            chr1   1           3        A    T    0.1   1.0
            chr1   11          13       A    G    0.2   2.0
            chr1   11          13       A    C    0.3   na
            chr1   11          13       A    T    0.4   na
            chr1   21          23       C    A    na    3.0
            chr1   21          23       C    G    na    4.0
            chr1   21          23       C    T    0.5   5.0
            chr1   31          33       C    A    na    3.0
            chr1   31          33       C    G    0.4   na
            chr1   31          33       C    T    na   5.0

            chr1   41          43       A    G    0.1   1.0
            chr1   41          43       A    C    0.1   1.0
            chr1   41          43       A    G    0.1   1.0

            chr3   1           13       A    G    0.3   3.0
            chr3   1           13       A    C    0.33  3.3
            chr3   10          13       A    G    0.3   3.0
            chr3   10          13       A    C    0.33  3.3

        """).strip(),
        seq_col=0, start_col=1, end_col=2, line_skip=1)
    res = build_filesystem_test_resource(root_path)
    score = build_score_from_resource(res)
    score.open()

    assert len(score.score_definitions) == 2
    assert "s1" in score.score_definitions
    assert "s2" in score.score_definitions

    return cast(NPScore, score)


@pytest.mark.parametrize("begin,end,scores,expected", [
    (5, 10, None, []),
    (1, 10, None, [
        (1, 3, [0.1, 1.0]),
        (1, 3, [0.1, 1.0]),
        (1, 3, [0.1, 1.0]),
    ]),
    (11, 20, None, [
        (11, 13, [0.2, 2.0]),
        (11, 13, [0.3, None]),
        (11, 13, [0.4, None]),
    ]),
    (21, 30, None, [
        (21, 23, [None, 3.0]),
        (21, 23, [None, 4.0]),
        (21, 23, [0.5, 5.]),
    ]),
    (31, 40, None, [
        (31, 33, [None, 3.0]),
        (31, 33, [0.4, None]),
        (31, 33, [None, 5.]),
    ]),
    (11, 20, ["s1"], [
        (11, 13, [0.2]),
        (11, 13, [0.3]),
        (11, 13, [0.4]),
    ]),
    (11, 20, ["s2"], [
        (11, 13, [2.0]),
        (11, 13, [None]),
        (11, 13, [None]),
    ]),
    (11, 20, ["s2", "s1"], [
        (11, 13, [2.0, 0.2]),
        (11, 13, [None, 0.3]),
        (11, 13, [None, 0.4]),
    ]),
    (41, 43, ["s1", "s2"], [
        (41, 43, [0.1, 1.0]),
        (41, 43, [0.1, 1.0]),
        (41, 43, [0.1, 1.0]),
    ]),
])
def test_np_score_fetch_regions(
    np_score: NPScore,
    begin: int | None,
    end: int | None,
    scores: list[str] | None,
    expected: list[tuple[int, int, list[ScoreValue]]],
) -> None:
    assert np_score is not None

    score_lines = list(
        np_score.fetch_region("chr1", begin, end, scores=scores))
    assert len(score_lines) == len(expected)
    assert score_lines == expected


@pytest.mark.parametrize("chrom,begin,end", [
    ("chr3", 1, 20),
])
def test_np_score_fetch_regions_consistency_failed(
    np_score: NPScore,
    chrom: str,
    begin: int | None,
    end: int | None,
) -> None:
    with pytest.raises(ValueError, match="multiple values for positions"):
        list(np_score.fetch_region(chrom, begin, end))


@pytest.fixture(scope="module")
def np_score2(tmp_path_factory: pytest.TempPathFactory) -> NPScore:
    root_path = tmp_path_factory.mktemp("np_score")
    setup_directories(
        root_path, {
        "genomic_resource.yaml": """
            type: np_score
            table:
                filename: data.txt.gz
                format: tabix
                reference:
                  name: ref
                alternative:
                  name: alt
            scores:
                - id: s1
                  type: float
                  name: s1

                - id: s2
                  type: float
                  name: s2
        """,
    })
    setup_tabix(
        root_path / "data.txt.gz",
        textwrap.dedent("""
            #chrom  pos_begin  ref  alt  s1    s2
            chr1    1          A    G    0.1   1.0
            chr1    1          A    C    0.1   1.0
            chr1    1          A    T    0.1   1.0
            chr1    11         A    G    0.2   2.0
            chr1    11         A    C    0.3   na
            chr1    11         A    T    0.4   na
            chr1    21         C    A    na    3.0
            chr1    21         C    G    na    4.0
            chr1    21         C    T    0.5   5.0
            chr1    31         C    A    na    3.0
            chr1    31         C    G    0.4   na
            chr1    31         C    T    na   5.0

            chr1    41         A    G    0.1   1.0
            chr1    41         A    C    0.1   1.0
            chr1    41         A    G    0.1   1.0

            chr1    51         A    G    0.3   3.0
            chr1    51         A    C    0.33  3.3

            chr1    60         A    G    0.3   3.0
            chr1    60         A    C    0.33  3.3
            chr1    60         A    G    0.3   3.0
            chr1    60         A    C    0.33  3.3

        """).strip(),
        seq_col=0, start_col=1, end_col=1, line_skip=1)
    res = build_filesystem_test_resource(root_path)
    score = build_score_from_resource(res)
    score.open()

    assert len(score.score_definitions) == 2
    assert "s1" in score.score_definitions
    assert "s2" in score.score_definitions

    return cast(NPScore, score)


@pytest.mark.parametrize("begin,end,scores,expected", [
    (5, 10, None, []),
    (1, 10, None, [
        (1, 1, [0.1, 1.0]),
        (1, 1, [0.1, 1.0]),
        (1, 1, [0.1, 1.0]),
    ]),
    (11, 20, None, [
        (11, 11, [0.2, 2.0]),
        (11, 11, [0.3, None]),
        (11, 11, [0.4, None]),
    ]),
    (21, 30, None, [
        (21, 21, [None, 3.0]),
        (21, 21, [None, 4.0]),
        (21, 21, [0.5, 5.]),
    ]),
    (31, 40, None, [
        (31, 31, [None, 3.0]),
        (31, 31, [0.4, None]),
        (31, 31, [None, 5.]),
    ]),
    (11, 20, ["s1"], [
        (11, 11, [0.2]),
        (11, 11, [0.3]),
        (11, 11, [0.4]),
    ]),
    (11, 20, ["s2"], [
        (11, 11, [2.0]),
        (11, 11, [None]),
        (11, 11, [None]),
    ]),
    (11, 20, ["s2", "s1"], [
        (11, 11, [2.0, 0.2]),
        (11, 11, [None, 0.3]),
        (11, 11, [None, 0.4]),
    ]),
    (41, 41, ["s1", "s2"], [
        (41, 41, [0.1, 1.0]),
        (41, 41, [0.1, 1.0]),
        (41, 41, [0.1, 1.0]),
    ]),
    (51, 51, ["s1", "s2"], [
        (51, 51, [0.3, 3.0]),
        (51, 51, [0.33, 3.3]),
    ]),
    (60, 60, ["s1", "s2"], [
        (60, 60, [0.3, 3.0]),
        (60, 60, [0.33, 3.3]),
        (60, 60, [0.3, 3.0]),
        (60, 60, [0.33, 3.3]),
    ]),
])
def test_np_score2_fetch_regions(
    np_score2: NPScore,
    begin: int | None,
    end: int | None,
    scores: list[str] | None,
    expected: list[tuple[int, int, list[ScoreValue]]],
) -> None:
    assert np_score2 is not None

    score_lines = list(
        np_score2.fetch_region("chr1", begin, end, scores=scores))
    assert len(score_lines) == len(expected)
    assert score_lines == expected


@pytest.fixture(scope="module")
def allele_score(tmp_path_factory: pytest.TempPathFactory) -> AlleleScore:
    root_path = tmp_path_factory.mktemp("np_score")
    setup_directories(
        root_path, {
        "genomic_resource.yaml": """
            type: allele_score
            table:
                filename: data.txt.gz
                format: tabix
                reference:
                  name: ref
                alternative:
                  name: alt
            scores:
                - id: s1
                  type: float
                  name: s1

                - id: s2
                  type: float
                  name: s2
        """,
    })
    setup_tabix(
        root_path / "data.txt.gz",
        textwrap.dedent("""
            #chrom  pos_begin  ref  alt  s1    s2
            chr1    1          A    G    0.1   1.0
            chr1    1          A    C    0.1   1.0
            chr1    1          A    AT   0.1   1.0
            chr1    11         A    G    0.2   2.0
            chr1    11         A    C    0.3   na
            chr1    11         A    AT   0.4   na
            chr1    21         C    A    na    3.0
            chr1    21         C    G    na    4.0
            chr1    21         C    T    0.5   5.0
            chr1    31         C    A    na    3.0
            chr1    31         C    G    0.4   na
            chr1    31         C    T    na   5.0

            chr2    1          A    AG   0.1   1.0
            chr2    1          A    G    0.1   1.0
            chr2    1          A    C    0.1   1.0
            chr2    1          A    AG   0.1   1.0

            chr3    1          A    AG   0.3   3.0
            chr3    1          A    C    0.33  3.3
            chr3    10         A    G    0.3   3.0
            chr3    10         A    C    0.33  3.3
            chr3    10         A    AG   0.3   3.0
            chr3    10         A    C    0.33  3.3

        """).strip(),
        seq_col=0, start_col=1, end_col=1, line_skip=1)
    res = build_filesystem_test_resource(root_path)
    score = build_score_from_resource(res)
    score.open()

    assert len(score.score_definitions) == 2
    assert "s1" in score.score_definitions
    assert "s2" in score.score_definitions

    return cast(AlleleScore, score)


@pytest.mark.parametrize("begin,end,scores,expected", [
    (5, 10, None, []),
    (1, 10, None, [
        (1, 1, [0.1, 1.0]),
        (1, 1, [0.1, 1.0]),
        (1, 1, [0.1, 1.0]),
    ]),
    (11, 20, None, [
        (11, 11, [0.2, 2.0]),
        (11, 11, [0.3, None]),
        (11, 11, [0.4, None]),
    ]),
    (21, 30, None, [
        (21, 21, [None, 3.0]),
        (21, 21, [None, 4.0]),
        (21, 21, [0.5, 5.]),
    ]),
    (31, 40, None, [
        (31, 31, [None, 3.0]),
        (31, 31, [0.4, None]),
        (31, 31, [None, 5.]),
    ]),
    (11, 20, ["s1"], [
        (11, 11, [0.2]),
        (11, 11, [0.3]),
        (11, 11, [0.4]),
    ]),
    (11, 20, ["s2"], [
        (11, 11, [2.0]),
        (11, 11, [None]),
        (11, 11, [None]),
    ]),
    (11, 20, ["s2", "s1"], [
        (11, 11, [2.0, 0.2]),
        (11, 11, [None, 0.3]),
        (11, 11, [None, 0.4]),
    ]),
])
def test_allele_score_fetch_regions(
    allele_score: AlleleScore,
    begin: int | None,
    end: int | None,
    scores: list[str] | None,
    expected: list[tuple[int, int, list[ScoreValue]]],
) -> None:
    assert allele_score is not None

    score_lines = list(
        allele_score.fetch_region("chr1", begin, end, scores=scores))
    assert len(score_lines) == len(expected)
    assert score_lines == expected


@pytest.mark.parametrize("chrom,begin,end", [
    ("chr2", 1, 10),
    ("chr3", 1, 20),
])
def test_allele_score_fetch_regions_consistency_failed(
    allele_score: AlleleScore,
    chrom: str,
    begin: int | None,
    end: int | None,
) -> None:
    with pytest.raises(ValueError, match="multiple values for positions"):
        list(allele_score.fetch_region(chrom, begin, end))
