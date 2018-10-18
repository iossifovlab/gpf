import pytest

from box import Box

from .utils import relative_to_this_test_folder

from annotation.tools.annotator_config import VariantAnnotatorConfig
from annotation.tools.score_annotator import VariantScoreAnnotator, \
    VariantMultiScoreAnnotator


input2_phast_exptected = \
    """RESULT_phastCons100way
-100
0.251
0.249
0.247
0.245
"""

input2_phast_pylo_expected = \
    """RESULT_phastCons100way\tRESULT_phyloP100way
-100\t-100
0.251\t0.061
0.249\t0.064
0.247\t0.061
0.245\t0.064
"""


@pytest.mark.parametrize("direct", [
    True,
    False
])
def test_variant_score_annotator_simple(variants_io, direct, capsys):

    options = Box({
        "vcf": True,
        "Graw": "fake_genome_ref_file",
        "direct": direct,
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

    score_annotator = VariantScoreAnnotator(config)
    assert score_annotator is not None

    captured = capsys.readouterr()

    with variants_io("fixtures/input2.tsv") as io_manager:
        score_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)
    assert captured.out == input2_phast_exptected


@pytest.mark.parametrize("direct", [
    True,
    False
])
def test_variant_multi_score_annotator_simple(variants_io, direct, capsys):

    options = Box({
        "vcf": True,
        "Graw": "fake_genome_ref_file",
        "direct": direct,
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

    score_annotator = VariantMultiScoreAnnotator(config)
    assert score_annotator is not None

    captured = capsys.readouterr()

    with variants_io("fixtures/input2.tsv") as io_manager:
        score_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)
    assert captured.out == input2_phast_exptected


@pytest.mark.parametrize("direct", [
    True,
    False
])
def test_variant_multi_score_annotator_multi(variants_io, direct, capsys):

    options = Box({
        "vcf": True,
        "Graw": "fake_genome_ref_file",
        "direct": direct,
        "scores_directory": relative_to_this_test_folder(
            "fixtures/")
    }, default_box=True, default_box_attr=None)

    columns_config = {
        'TESTphastCons100way': "RESULT_phastCons100way",
        'TESTphyloP100way': "RESULT_phyloP100way",
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

    score_annotator = VariantMultiScoreAnnotator(config)
    assert score_annotator is not None

    captured = capsys.readouterr()

    with variants_io("fixtures/input2.tsv") as io_manager:
        score_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)
    assert captured.out == input2_phast_pylo_expected
