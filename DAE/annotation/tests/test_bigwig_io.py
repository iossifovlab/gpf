import pytest

from .conftest import relative_to_this_test_folder
from annotation.tools.score_file_io import ScoreFile
try:
    bigwig_enabled = True
    from annotation.tools.score_file_io_bigwig import BigWigLineAdapter
except ImportError:
    bigwig_enabled = False


@pytest.mark.skipif(bigwig_enabled is False,
                    reason='pyBigWig module is not installed')
def test_bigwig_header():
    score_filename = relative_to_this_test_folder(
        "fixtures/TESTbigwig/TEST_bigwig_score.bw")

    bw_score_file = ScoreFile(score_filename)
    assert bw_score_file is not None
    assert bw_score_file.header == ['chrom', 'chromStart', 'chromEnd',
                                    'TEST_bigwig_score']


@pytest.mark.skipif(bigwig_enabled is False,
                    reason='pyBigWig module is not installed')
def test_bigwig_access_simple():
    score_filename = relative_to_this_test_folder(
        "fixtures/TESTbigwig/TEST_bigwig_score.bw")

    bw_score_file = ScoreFile(score_filename)
    assert bw_score_file is not None

    res = bw_score_file.fetch_scores_df("1", 1, 1)
    print(res)
    assert len(res) == 1
    assert float(res['TEST_bigwig_score'][0]) == \
        pytest.approx(0.7, 1E-3)

    res = bw_score_file.fetch_scores_df("20", 207, 207)
    print(res)
    assert len(res) == 1
    assert float(res['TEST_bigwig_score'][0]) == \
        pytest.approx(22.4, 1E-3)

    res = bw_score_file.fetch_scores_df("X", 235, 235)
    print(res)
    assert len(res) == 1
    assert float(res['TEST_bigwig_score'][0]) == \
        pytest.approx(22.7, 1E-3)


@pytest.mark.skipif(bigwig_enabled is False,
                    reason='pyBigWig module is not installed')
def test_bigwig_line_adapter():
    score_filename = relative_to_this_test_folder(
        "fixtures/TESTbigwig/TEST_bigwig_score.bw")

    bw_score_file = ScoreFile(score_filename)
    bwline = BigWigLineAdapter(bw_score_file, 'chr1', [0, 1, 0.1234])

    assert bwline.chrom == 'chr1'
    assert bwline.pos_begin == 1
    assert bwline.pos_end == 1

    assert bwline[1] == bwline.pos_begin
