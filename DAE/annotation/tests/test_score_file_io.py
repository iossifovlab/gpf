import pytest

from .conftest import relative_to_this_test_folder
from annotation.tools.score_file_io import \
    ScoreFile, LineAdapter, LineBufferAdapter


def test_regions_intersecting():
    regions = [
        # subset
        ((10918, 11018), (10958, 11018)),
        # overlap
        ((10918, 11018), (10958, 11058)),
        # overlap single
        ((10918, 11018), (11018, 11058))
    ]
    for region_pair in regions:
        assert LineBufferAdapter.regions_intersect(*region_pair[0],
                                                   *region_pair[1])
        assert LineBufferAdapter.regions_intersect(*region_pair[1],
                                                   *region_pair[0])


def test_regions_non_intersecting():
    regions = [
        # tangent
        ((10918, 11018), (11019, 11059)),
        # gapped
        ((10918, 11018), (12918, 13018))
    ]
    for region_pair in regions:
        assert not LineBufferAdapter.regions_intersect(*region_pair[0],
                                                       *region_pair[1])
        assert not LineBufferAdapter.regions_intersect(*region_pair[1],
                                                       *region_pair[0])


# @pytest.mark.parametrize("score_filename,no_header", [
#     ("fixtures/TESTphastCons100way/TESTphastCons100way.bedGraph.gz", True),
#     ("fixtures/TEST3phastCons100way/TEST3phastCons100way.bedGraph.gz", True),
# ])
# def test_score_file_header(score_filename, no_header):
#     score_filename = relative_to_this_test_folder(score_filename)
#     score_config_filename = None
#     options = Box({}, default_box=True, default_box_attr=None)
#
#     with IterativeAccess(
#             options, score_filename, score_config_filename) as score_io:
#         assert score_io is not None
#         if no_header:
#             assert score_io.options.no_header
#         else:
#             assert not score_io.options.no_header


def test_iterative_access_simple():
    score_filename = relative_to_this_test_folder(
        "fixtures/TESTphastCons100way/TESTphastCons100way.bedGraph.gz")

    score_file = ScoreFile(score_filename)
    assert score_file is not None

    res = score_file.fetch_scores_df("1", 10918, 10920)
    print(res)

    res = score_file.fetch_scores_df("1", 10934, 10934)

    assert len(res) == 1

    assert float(res['TESTphastCons100way'][0]) == \
        pytest.approx(0.204, 1E-3)


def test_iterative_line_adapter():
    score_filename = relative_to_this_test_folder(
        "fixtures/TESTphastCons100way/TESTphastCons100way.bedGraph.gz")

    score_file = ScoreFile(score_filename)
    assert score_file is not None

    line = LineAdapter(
        score_file, ["1", "10", "20", "1", "10", "20", "30"])

    assert line.pos_begin == 10


def test_direct_access_simple():
    score_filename = relative_to_this_test_folder(
        "fixtures/TESTphastCons100way/TESTphastCons100way.bedGraph.gz")

    score_file = ScoreFile(score_filename, direct=True)

    assert score_file is not None

    res = score_file.fetch_scores_df("1", 10934, 10934)
    print(res)

    assert len(res) == 1

    assert float(res['TESTphastCons100way'][0]) == \
        pytest.approx(0.204, 1E-3)


def test_iterative_access_with_reset_backward(mocker):
    score_filename = relative_to_this_test_folder(
        "fixtures/TEST3phastCons100way/TEST3phastCons100way.bedGraph.gz")

    score_file = ScoreFile(score_filename)
    assert score_file is not None

    check_pos = 20005
    res = score_file.fetch_scores_df("1", check_pos, check_pos)
    print(res)
    assert len(res) == 1
    assert res['chromStart'][0] <= check_pos and \
        res['chromEnd'][0] >= check_pos

    mocker.spy(score_file.accessor, '_region_reset')

    check_pos = 20001
    res = score_file.fetch_scores_df("1", check_pos, check_pos)
    print(res)
    assert len(res) == 1
    assert res['chromStart'][0] <= check_pos and \
        res['chromEnd'][0] >= check_pos

    assert score_file.accessor._region_reset.call_count == 1
    print(dir(score_file.accessor._region_reset))
    print(score_file.accessor._region_reset.call_args)
    score_file.accessor._region_reset.assert_called_once_with("1:20001")


def test_iterative_access_with_reset_different_chrom(mocker):
    score_filename = relative_to_this_test_folder(
        "fixtures/TEST3phastCons100way/TEST3phastCons100way.bedGraph.gz")

    score_file = ScoreFile(score_filename)
    assert score_file is not None

    check_pos = 20000
    res = score_file.fetch_scores_df("1", check_pos, check_pos)
    print(res)
    assert len(res) == 1
    assert res['chromStart'][0] <= check_pos and \
        res['chromEnd'][0] >= check_pos

    mocker.spy(score_file.accessor, '_region_reset')

    check_pos = 20001
    res = score_file.fetch_scores_df("2", check_pos, check_pos)
    print(res)
    assert len(res) == 1
    assert res['chromStart'][0] <= check_pos and \
        res['chromEnd'][0] >= check_pos

    print(score_file.accessor._region_reset.call_args)

    assert score_file.accessor._region_reset.call_count == 1
    print(dir(score_file.accessor._region_reset))
    print(score_file.accessor._region_reset.call_args)
    # score_io._region_reset.assert_called_once()
    score_file.accessor._region_reset.assert_called_once_with("2:20001")


def test_iterative_access_with_reset_long_jump_ahead(mocker):
    score_filename = relative_to_this_test_folder(
        "fixtures/TEST3phastCons100way/TEST3phastCons100way.bedGraph.gz")

    score_file = ScoreFile(score_filename)
    assert score_file is not None

    check_pos = 20000
    res = score_file.fetch_scores_df("1", check_pos, check_pos)
    print(res)
    assert len(res) == 1
    assert res['chromStart'][0] <= check_pos and \
        res['chromEnd'][0] >= check_pos

    score_file.accessor.LONG_JUMP_THRESHOLD = 3
    mocker.spy(score_file.accessor, '_region_reset')

    check_pos = 20005
    res = score_file.fetch_scores_df("1", check_pos, check_pos)
    print(res)
    assert len(res) == 1
    assert res['chromStart'][0] <= check_pos and \
        res['chromEnd'][0] >= check_pos

    assert score_file.accessor._region_reset.call_count == 1
    print(dir(score_file.accessor._region_reset))
    print(score_file.accessor._region_reset.call_args)
    score_file.accessor._region_reset.assert_called_once_with("1:20005")


@pytest.mark.parametrize("chrom,pos_start,pos_end,count", [
    ("7", 20000, 20000, 1),
    ("7", 19999, 20000, 1),
    ("7", 19999, 20005, 5),
])
def test_iterative_access_with_na_values(chrom, pos_start, pos_end, count):
    score_filename = relative_to_this_test_folder(
        "fixtures/TEST3phastCons100way/TEST3phastCons100way.bedGraph.gz")

    score_file = ScoreFile(score_filename)
    assert score_file is not None

    res = score_file.fetch_scores_df(chrom, pos_start, pos_end)
    print(res)
    assert len(res) == count
    assert res['chromStart'][0] <= pos_start and \
        res['chromEnd'][count-1] >= pos_end


def test_aggregation_correctness():
    score_filename = relative_to_this_test_folder(
        "fixtures/TESTphastCons100way/TESTphastCons100way.bedGraph.gz")

    score_file = ScoreFile(score_filename)
    assert score_file is not None

    res = score_file.fetch_scores_df('1', 10937, 10939)
    print(res)
    assert sum(res['COUNT']) == 3
