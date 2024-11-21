# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
from typing import cast

import pytest

from dae.genomic_resources.genomic_scores import (
    PositionScore,
    PositionScoreQuery,
    ScoreValue,
    build_score_from_resource,
)
from dae.genomic_resources.testing import (
    build_filesystem_test_resource,
    setup_directories,
    setup_tabix,
)


@pytest.fixture(scope="module")
def position_multiscore(
    tmp_path_factory: pytest.TempPathFactory,
) -> PositionScore:
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
                allow_multiple_values: true
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
        chr3     61        73       7.0    70.0
        """).strip(),
        seq_col=0, start_col=1, end_col=2)
    res = build_filesystem_test_resource(root_path)
    score = build_score_from_resource(res)
    score.open()
    assert len(score.score_definitions) == 2
    assert "s1" in score.score_definitions
    assert "s2" in score.score_definitions
    return cast(PositionScore, score)


@pytest.mark.parametrize("chrom,begin,end,scores,expected", [
    ("chr2", 60, 120, ["s1", "s2"], [
        (61, 73, [6.0, 60.0]),
        (71, 73, [7.0, 70.0]),
    ]),
    ("chr3", 60, 120, ["s1", "s2"], [
        (61, 73, [6.0, 60.0]),
        (61, 73, [7.0, 70.0]),
    ]),
])
def test_position_multiscore_fetch_region(
    position_multiscore: PositionScore,
    chrom: str,
    begin: int | None,
    end: int | None,
    scores: list[str] | None,
    expected: list[tuple[int, int, list[ScoreValue]]],
) -> None:

    lines = list(position_multiscore.fetch_region(chrom, begin, end, scores))
    assert len(lines) == 2
    assert lines == expected


@pytest.mark.parametrize("chrom,pos,scores,expected", [
    ("chr2", 71, ["s1", "s2"], [6.5, 65.0]),
    ("chr2", 71, [PositionScoreQuery("s1", "max")], [7.0]),
    ("chr2", 71, [PositionScoreQuery("s2", "max")], [70.0]),
    ("chr2", 71, [PositionScoreQuery("s1", "min")], [6.0]),
    ("chr2", 71, [PositionScoreQuery("s2", "min")], [60.0]),
])
def test_position_multiscore_fetch_score(
    position_multiscore: PositionScore,
    chrom: str,
    pos: int,
    scores: list[str] | None,
    expected: list[ScoreValue],
) -> None:

    res = position_multiscore.fetch_scores(chrom, pos, scores)
    assert res is not None
    assert len(res) == len(expected)
    assert res == expected
