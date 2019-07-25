import pytest
import pandas as pd

from collections import OrderedDict
from box import Box

from .conftest import relative_to_this_test_folder

from annotation.tools.annotator_config import VariantAnnotatorConfig
from annotation.tools.score_annotator import PositionScoreAnnotator, \
    PositionMultiScoreAnnotator, NPScoreAnnotator
try:
    bigwig_enabled = True
    from annotation.tools.score_file_io_bigwig import BigWigAccess  # noqa
except ImportError:
    bigwig_enabled = False


input2_phast_exptected = \
    """RESULT_phastCons100way
0.253
0.251
0.249
0.247
0.245
"""

input2_phast_pylo_expected = \
    """RESULT_phastCons100way\tRESULT_phyloP100way
0.253\t0.064
0.251\t0.061
0.249\t0.064
0.247\t0.061
0.245\t0.064
"""


@pytest.mark.parametrize("direct", [
    True,
    False
])
def test_variant_score_annotator_simple(
        expected_df, variants_io, direct, capsys):

    options = Box({
        "vcf": True,
        "Graw": "fake_genome_ref_file",
        "direct": direct,
        "mode": "overwrite",
        "scores_file": relative_to_this_test_folder(
            "fixtures/TESTphastCons100way/TESTphastCons100way.bedGraph.gz")
    }, default_box=True, default_box_attr=None)

    columns_config = {
        'TESTphastCons100way': "RESULT_phastCons100way",
    }

    config = VariantAnnotatorConfig(
        name="test_annotator",
        annotator_name="score_annotator.VariantScoreAnnotator",
        options=options,
        columns_config=columns_config,
        virtuals=[]
    )
    print(config.options)
    print(type(config.options))

    with variants_io("fixtures/input2.tsv") as io_manager:
        score_annotator = PositionScoreAnnotator(config)
        assert score_annotator is not None

        captured = capsys.readouterr()

        score_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)
    pd.testing.assert_frame_equal(
        expected_df(captured.out),
        expected_df(input2_phast_exptected),
        check_less_precise=3)


@pytest.mark.parametrize("direct", [
    True,
    False
])
def test_variant_multi_score_annotator_simple(
        expected_df, variants_io, direct, capsys):

    options = Box({
        "vcf": True,
        "Graw": "fake_genome_ref_file",
        "direct": direct,
        "mode": "overwrite",
        "scores_directory": relative_to_this_test_folder(
            "fixtures/")
    }, default_box=True, default_box_attr=None)

    columns_config = {
        'TESTphastCons100way': "RESULT_phastCons100way",
    }

    config = VariantAnnotatorConfig(
        name="test_annotator",
        annotator_name="score_annotator.VariantScoreAnnotator",
        options=options,
        columns_config=columns_config,
        virtuals=[]
    )
    print(config.options)
    print(type(config.options))

    with variants_io("fixtures/input2.tsv") as io_manager:
        score_annotator = PositionMultiScoreAnnotator(config)
        assert score_annotator is not None

        captured = capsys.readouterr()

        score_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)

    pd.testing.assert_frame_equal(
        expected_df(captured.out),
        expected_df(input2_phast_exptected),
        check_less_precise=3)


@pytest.mark.parametrize("direct", [
    True,
    False
])
def test_variant_multi_score_annotator_multi(
        expected_df, variants_io, direct, capsys):

    options = Box({
        "vcf": True,
        "Graw": "fake_genome_ref_file",
        "direct": direct,
        "mode": "overwrite",
        "scores_directory": relative_to_this_test_folder(
            "fixtures/")
    }, default_box=True, default_box_attr=None)

    columns_config = OrderedDict([
        ('TESTphastCons100way',  "RESULT_phastCons100way"),
        ('TESTphyloP100way', "RESULT_phyloP100way"),
    ])

    config = VariantAnnotatorConfig(
        name="test_annotator",
        annotator_name="score_annotator.VariantScoreAnnotator",
        options=options,
        columns_config=columns_config,
        virtuals=[]
    )
    print(config.options)
    print(type(config.options))

    with variants_io("fixtures/input2.tsv") as io_manager:
        score_annotator = PositionMultiScoreAnnotator(config)
        assert score_annotator is not None

        captured = capsys.readouterr()

        score_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)
    pd.testing.assert_frame_equal(
        expected_df(captured.out),
        expected_df(input2_phast_pylo_expected),
        check_less_precise=3)


input2_cadd_expected = """RESULT_RawScore\tRESULT_PHRED
0.40161\t6.631
0.537788\t7.986
0.371362\t6.298
0.537794\t7.986
0.391539\t6.522
"""


@pytest.mark.parametrize("direct", [
    True,
    False
])
def test_variant_score_annotator_cadd(
        expected_df, variants_io, direct, capsys):

    options = Box({
        "vcf": True,
        "Graw": "fake_genome_ref_file",
        "direct": direct,
        "mode": "overwrite",
        "scores_file": relative_to_this_test_folder(
            "fixtures/TESTCADD/TESTwhole_genome_SNVs.tsv.gz"),
        "search_columns": "VCF:ref,VCF:alt",
    }, default_box=True, default_box_attr=None)

    columns_config = OrderedDict([
        ('RawScore',  "RESULT_RawScore"),
        ('PHRED', "RESULT_PHRED"),
    ])

    config = VariantAnnotatorConfig(
        name="test_annotator",
        annotator_name="score_annotator.VariantScoreAnnotator",
        options=options,
        columns_config=columns_config,
        virtuals=[]
    )
    print(config.options)
    print(type(config.options))

    with variants_io("fixtures/input2.tsv") as io_manager:
        score_annotator = NPScoreAnnotator(config)
        assert score_annotator is not None

        captured = capsys.readouterr()

        score_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)

    pd.testing.assert_frame_equal(
        expected_df(captured.out),
        expected_df(input2_cadd_expected),
        check_less_precise=3)
