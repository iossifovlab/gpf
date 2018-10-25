import pytest

from box import Box

from .utils import relative_to_this_test_folder
from annotation.tools.score_file_io import \
    DirectAccess, IterativeAccess


def test_iterative_access_simple():
    score_filename = relative_to_this_test_folder(
        "fixtures/TESTphastCons100way/TESTphastCons100way.bedGraph.gz")
    score_config_filename = None
    options = Box({}, default_box=True, default_box_attr=None)

    with IterativeAccess(
            options, score_filename, score_config_filename) as score_io:
        assert score_io is not None

        res = score_io.fetch_scores_df("1", 10918, 10920)
        print(res)

        res = score_io.fetch_scores_df("1", 10934, 10934)

        assert len(res) == 1

        assert float(res['TESTphastCons100way'][0]) == \
            pytest.approx(0.204, 1E-3)


def test_direct_access_simple():
    score_filename = relative_to_this_test_folder(
        "fixtures/TESTphastCons100way/TESTphastCons100way.bedGraph.gz")
    score_config_filename = None

    options = Box({}, default_box=True, default_box_attr=None)
    with DirectAccess(
            options, score_filename, score_config_filename) as score_io:

        assert score_io is not None

        res = score_io.fetch_scores_df("1", 10934, 10934)
        print(res)

        assert len(res) == 1

        assert float(res['TESTphastCons100way'][0]) == \
            pytest.approx(0.204, 1E-3)
