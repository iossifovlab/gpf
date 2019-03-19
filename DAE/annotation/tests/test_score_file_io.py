import pytest

from .conftest import relative_to_this_test_folder
from annotation.tools.score_file_io import \
    ScoreFile, TabixAccess, LineAdapter, LineBufferAdapter


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
        assert LineBufferAdapter.regions_intersect(region_pair[0][0],
                                                   region_pair[0][1],
                                                   region_pair[1][0],
                                                   region_pair[1][1])
        assert LineBufferAdapter.regions_intersect(region_pair[1][0],
                                                   region_pair[1][1],
                                                   region_pair[0][0],
                                                   region_pair[0][1])


def test_regions_non_intersecting():
    regions = [
        # tangent
        ((10918, 11018), (11019, 11059)),
        # gapped
        ((10918, 11018), (12918, 13018))
    ]
    for region_pair in regions:
        assert not LineBufferAdapter.regions_intersect(region_pair[0][0],
                                                       region_pair[0][1],
                                                       region_pair[1][0],
                                                       region_pair[1][1])
        assert not LineBufferAdapter.regions_intersect(region_pair[1][0],
                                                       region_pair[1][1],
                                                       region_pair[0][0],
                                                       region_pair[0][1])


def test_load_config():
    score_filename = relative_to_this_test_folder(
        "fixtures/TESTphastCons100way/TESTphastCons100way.bedGraph.gz")
    config_filename = \
        relative_to_this_test_folder('fixtures/sample_score_config.conf')

    dummy_score = ScoreFile(score_filename, config_filename)

    expected_header = ['chrom', 'chromStart', 'chromEnd',
                       'scoreOne', 'scoreTwo', 'scoreThree',
                       'scoreFour', 'scoreFive']

    assert dummy_score.header == expected_header
    assert dummy_score.score_names == expected_header[3:]
    assert all([col in dummy_score.schema for col in expected_header])


def test_tabix_threshold_values():
    assert TabixAccess.LONG_JUMP_THRESHOLD == 5000
    assert TabixAccess.ACCESS_SWITCH_THRESHOLD == 1500


def test_line_adapter(score_file):
    score_filename = relative_to_this_test_folder(
        "fixtures/TESTphastCons100way/TESTphastCons100way.bedGraph.gz")

    score_file = ScoreFile(score_filename)
    assert score_file is not None

    line = LineAdapter(score_file, ["1", "10", "20", "1", "10", "20", "30"])
    assert line.pos_begin == 10


@pytest.mark.parametrize("access_type", ['sequential', 'direct'])
def test_tabix_accessors_simple(score_file, access_type):
    if access_type == 'sequential':
        res = score_file.accessor._fetch_sequential('1', 10918, 10920)
        res = score_file.accessor._fetch_sequential('1', 10934, 10934)
    else:
        res = score_file.accessor._fetch_direct('1', 10934, 10934)

    assert len(res) == 1
    assert len(res[0].line) == len(res[0])
    assert float(res[0][3]) == pytest.approx(0.204, 1E-3)


def test_tabix_sequential_access_reset_backward(score_file, mocker):
    mocker.spy(score_file.accessor, '_region_reset')
    for check_pos in [20005, 20001]:
        res = score_file.accessor._fetch_sequential('1', check_pos, check_pos)
        assert len(res) == 1
        assert res[0][1] <= check_pos and \
            res[0][2] >= check_pos

    assert score_file.accessor._region_reset.call_count == 2
    score_file.accessor._region_reset.assert_called_with("1:20001")


def test_tabix_sequential_access_reset_different_chrom(score_file, mocker):
    mocker.spy(score_file.accessor, '_region_reset')
    for chrom, check_pos in [('1', 20000), ('2', 20001)]:
        res = score_file.accessor._fetch_sequential(chrom,
                                                    check_pos, check_pos)
        assert len(res) == 1
        assert res[0][1] <= check_pos and \
            res[0][2] >= check_pos

    assert score_file.accessor._region_reset.call_count == 2
    score_file.accessor._region_reset.assert_called_with("2:20001")


def test_tabix_sequential_access_reset_long_jump_ahead(score_file, mocker):
    score_file.accessor.LONG_JUMP_THRESHOLD = 3
    mocker.spy(score_file.accessor, '_region_reset')
    for check_pos in [20000, 20005]:
        res = score_file.accessor._fetch_sequential('1', check_pos, check_pos)
        assert len(res) == 1
        assert res[0][1] <= check_pos and \
            res[0][2] >= check_pos

    assert score_file.accessor._region_reset.call_count == 2
    score_file.accessor._region_reset.assert_called_with("1:20005")


@pytest.mark.parametrize("chrom,pos_start,pos_end,count", [
    ("7", 20000, 20000, 1),
    ("7", 19999, 20000, 1),
    ("7", 19999, 20005, 5),
])
def test_tabix_sequential_access_na_values(score_file, chrom,
                                           pos_start, pos_end, count):
    res = score_file.accessor._fetch_sequential(chrom, pos_start, pos_end)
    assert len(res) == count
    assert res[0][1] <= pos_start and \
        res[count-1][2] >= pos_end


def test_tabix_access_switching(score_file, mocker):
    mocker.spy(score_file.accessor, '_fetch_sequential')
    mocker.spy(score_file.accessor, '_fetch_direct')
    
    # inital fetch will use direct, as (10937 - 0) is above the threshold
    res = score_file.fetch_scores('1', 10937, 10937)
    assert score_file.accessor._fetch_direct.call_count == 1
    
    # fetch substitution that is close
    res = score_file.fetch_scores('1', 10938, 10938)
    assert score_file.accessor._fetch_sequential.call_count == 1
    
    # fetch substitution that is beyond threshold
    res = score_file.fetch_scores('1', 12439, 12439)
    assert score_file.accessor._fetch_direct.call_count == 2
    
    # fetch substitution that is close, but behind
    res = score_file.fetch_scores('1', 12437, 12437)
    assert score_file.accessor._fetch_sequential.call_count == 2
    
    # fetch insertion that is close
    res = score_file.fetch_scores('1', 12438, 12439)
    assert score_file.accessor._fetch_sequential.call_count == 3
    
    # fetch insertion that is beyond threshold
    res = score_file.fetch_scores('1', 13940, 13941)
    assert score_file.accessor._fetch_direct.call_count == 3
    
    # fetch deletion that is close
    res = score_file.fetch_scores('1', 13941, 13950)
    assert score_file.accessor._fetch_sequential.call_count == 4
    
    # fetch deletion that is beyond threshold
    res = score_file.fetch_scores('1', 16000, 16050)
    assert score_file.accessor._fetch_direct.call_count == 4


def test_aggregation_correctness(score_file):
    res = score_file.fetch_scores_df('1', 10937, 10939)
    print(res)
    assert sum(res['COUNT']) == 3
