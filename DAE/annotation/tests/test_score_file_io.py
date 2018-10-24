import pytest
from .utils import relative_to_this_test_folder
from annotation.tools.score_file_io import IterativeAccess, \
    DirectAccess


def test_iterative_access_simple():
    score_filename = relative_to_this_test_folder(
        "fixtures/TESTphastCons100way/TESTphastCons100way.bedGraph.gz")
    score_config = None

    score_io = IterativeAccess(score_filename, score_config)
    assert score_io is not None

    res = score_io.fetch_score_lines("1", 10918, 10920)
    print(res)

    res = score_io.fetch_score_lines("1", 10934, 10934)

    assert len(res) == 1

    assert float(res['TESTphastCons100way'][0]) == \
        pytest.approx(0.204, 1E-3)


def test_direct_access_simple():
    score_filename = relative_to_this_test_folder(
        "fixtures/TESTphastCons100way/TESTphastCons100way.bedGraph.gz")
    score_config = None

    score_io = DirectAccess(score_filename, score_config)
    assert score_io is not None

    res = score_io.fetch_score_lines("1", 10934, 10934)

    assert len(res) == 1

    assert float(res['TESTphastCons100way'][0]) == \
        pytest.approx(0.204, 1E-3)
