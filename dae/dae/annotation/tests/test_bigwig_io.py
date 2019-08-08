import pytest

import pandas as pd
from .conftest import relative_to_this_test_folder
from box import Box
from dae.annotation.tools.score_file_io import ScoreFile
from dae.annotation.tools.score_annotator import PositionScoreAnnotator
from dae.annotation.tools.annotator_config import VariantAnnotatorConfig
try:
    bigwig_enabled = True
    from dae.annotation.tools.score_file_io_bigwig import \
        BigWigAccess, BigWigLineAdapter
except ImportError:
    bigwig_enabled = False


expected_bw_output = """RESULT_bigwig_score
0.8166
1.05
22.0111
21.7
22.7
23.05
"""


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
def test_bigwig_access_indels(expected_df, capsys, variants_io):

    options = Box({
        "mode": "overwrite",
        "scores_file": relative_to_this_test_folder(
            "fixtures/TESTbigwig/TEST_bigwig_score.bw")
    }, default_box=True, default_box_attr=None)

    config = VariantAnnotatorConfig(
        name="test_bigwig_annotator",
        annotator_name="score_annotator.PositionScoreAnnotator",
        options=options,
        columns_config={'TEST_bigwig_score': "RESULT_bigwig_score"},
        virtuals=[]
    )
    print(config.options)
    print(type(config.options))

    with variants_io("fixtures/bigwig_indels.tsv") as io_manager:
        score_annotator = PositionScoreAnnotator(config)
        assert score_annotator is not None
        assert isinstance(score_annotator.score_file.accessor, BigWigAccess)
        captured = capsys.readouterr()
        score_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)
    pd.testing.assert_frame_equal(
        expected_df(captured.out),
        expected_df(expected_bw_output),
        check_less_precise=3)
