import pytest


from .conftest import relative_to_this_test_folder
try:
    bigwig_enabled = True
    from annotation.tools.score_file_io_bigwig import \
        BigWigFile, BigWigLineAdapter
except ImportError:
    bigwig_enabled = False


@pytest.mark.skipif(bigwig_enabled is False,
                    reason='pyBigWig module is not installed')
def test_bigwig_header():
    score_filename = relative_to_this_test_folder(
        "fixtures/TESTbigwig/TEST_bigwig_score.bw")
    score_config_filename = None

    with BigWigFile(score_filename, score_config_filename) as bigwig_io:
        assert bigwig_io is not None
        assert bigwig_io.header == ['chrom', 'pos_begin', 'pos_end',
                                    'TEST_bigwig_score']


@pytest.mark.skipif(bigwig_enabled is False,
                    reason='pyBigWig module is not installed')
def test_bigwig_access_simple():
    score_filename = relative_to_this_test_folder(
        "fixtures/TESTbigwig/TEST_bigwig_score.bw")
    score_config_filename = None

    with BigWigFile(score_filename, score_config_filename) as bigwig_io:
        assert bigwig_io is not None

        res = bigwig_io.fetch_scores_df("1", 1, 1)
        print(res)
        assert len(res) == 1
        assert float(res['TEST_bigwig_score'][0]) == \
            pytest.approx(0.7, 1E-3)

        res = bigwig_io.fetch_scores_df("20", 207, 207)
        print(res)
        assert len(res) == 1
        assert float(res['TEST_bigwig_score'][0]) == \
            pytest.approx(22.4, 1E-3)

        res = bigwig_io.fetch_scores_df("X", 235, 235)
        print(res)
        assert len(res) == 1
        assert float(res['TEST_bigwig_score'][0]) == \
            pytest.approx(22.7, 1E-3)


@pytest.mark.skipif(bigwig_enabled is False,
                    reason='pyBigWig module is not installed')
def test_bigwig_line_adapter():
    bwline = BigWigLineAdapter('chr1', [0, 1, 0.1234])

    assert bwline.chrom == 'chr1'
    assert bwline.pos_begin == 1
    assert bwline.pos_end == 1

    assert bwline[1] == bwline.pos_begin
