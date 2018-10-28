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


def test_iterative_access_with_reset_backward(mocker):
    score_filename = relative_to_this_test_folder(
        "fixtures/TEST3phastCons100way/TEST3phastCons100way.bedGraph.gz")
    score_config_filename = None
    options = Box({}, default_box=True, default_box_attr=None)

    with IterativeAccess(
            options, score_filename, score_config_filename) as score_io:
        assert score_io is not None

        check_pos = 20005
        res = score_io.fetch_scores_df("1", check_pos, check_pos)
        print(res)
        assert len(res) == 1
        assert res['chromStart'][0] <= check_pos and \
            res['chromEnd'][0] >= check_pos

        mocker.spy(score_io, '_region_reset')

        check_pos = 20001
        res = score_io.fetch_scores_df("1", check_pos, check_pos)
        print(res)
        assert len(res) == 1
        assert res['chromStart'][0] <= check_pos and \
            res['chromEnd'][0] >= check_pos

        assert score_io._region_reset.call_count == 1
        print(dir(score_io._region_reset))
        print(score_io._region_reset.call_args)
        # score_io._region_reset.assert_called_once()
        score_io._region_reset.assert_called_once_with("1:20001")


def test_iterative_access_with_reset_different_chrom(mocker):
    score_filename = relative_to_this_test_folder(
        "fixtures/TEST3phastCons100way/TEST3phastCons100way.bedGraph.gz")
    score_config_filename = None
    options = Box({}, default_box=True, default_box_attr=None)

    with IterativeAccess(
            options, score_filename, score_config_filename) as score_io:
        assert score_io is not None

        check_pos = 20000
        res = score_io.fetch_scores_df("1", check_pos, check_pos)
        print(res)
        assert len(res) == 1
        assert res['chromStart'][0] <= check_pos and \
            res['chromEnd'][0] >= check_pos

        mocker.spy(score_io, '_region_reset')

        check_pos = 20001
        res = score_io.fetch_scores_df("2", check_pos, check_pos)
        print(res)
        assert len(res) == 1
        assert res['chromStart'][0] <= check_pos and \
            res['chromEnd'][0] >= check_pos

        print(score_io._region_reset.call_args)

        assert score_io._region_reset.call_count == 1
        print(dir(score_io._region_reset))
        print(score_io._region_reset.call_args)
        # score_io._region_reset.assert_called_once()
        score_io._region_reset.assert_called_once_with("2:20001")


def test_iterative_access_with_reset_long_jump_ahead(mocker):
    score_filename = relative_to_this_test_folder(
        "fixtures/TEST3phastCons100way/TEST3phastCons100way.bedGraph.gz")
    score_config_filename = None
    options = Box({}, default_box=True, default_box_attr=None)

    with IterativeAccess(
            options, score_filename, score_config_filename) as score_io:
        assert score_io is not None

        check_pos = 20000
        res = score_io.fetch_scores_df("1", check_pos, check_pos)
        print(res)
        assert len(res) == 1
        assert res['chromStart'][0] <= check_pos and \
            res['chromEnd'][0] >= check_pos

        score_io.LONG_JUMP_THRESHOLD = 3
        mocker.spy(score_io, '_region_reset')

        check_pos = 20005
        res = score_io.fetch_scores_df("1", check_pos, check_pos)
        print(res)
        assert len(res) == 1
        assert res['chromStart'][0] <= check_pos and \
            res['chromEnd'][0] >= check_pos

        assert score_io._region_reset.call_count == 1
        print(dir(score_io._region_reset))
        print(score_io._region_reset.call_args)
        # score_io._region_reset.assert_called_once()
        score_io._region_reset.assert_called_once_with("1:20005")
