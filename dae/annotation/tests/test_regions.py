import pytest
import pandas as pd

from box import Box

from .conftest import relative_to_this_test_folder

from dae.annotation.tools.annotator_config import VariantAnnotatorConfig
from dae.annotation.tools.score_annotator import PositionScoreAnnotator


phast_chr1_2 = """CHROM	POS	REF	ALT	RESULT_phastCons100way
chr1	20003	T	A	0.001
chr1	20004	G	A	0.0
"""

phylo_chr1_2 = """CHROM	POS	REF	ALT	RESULT_phyloP100way
chr1	20003	T	A	0.023
chr1	20004	G	A	-0.036
"""

phast_chr2_2 = """CHROM	POS	REF	ALT	RESULT_phastCons100way
chr2	20003	G	T	0.011
chr2	20004	G	A	0.004
"""

phylo_chr2_2 = """CHROM	POS	REF	ALT	RESULT_phyloP100way
chr2	20003	G	T	1.208
chr2	20004	G	A	-0.118
"""


@pytest.mark.parametrize("direct,score_name,region,expected", [
    (True, 'phastCons100way', "chr1:20003-20004", phast_chr1_2),
    (False, 'phastCons100way', "chr1:20003-20004", phast_chr1_2),
    (True, 'phyloP100way', "chr1:20003-20004", phylo_chr1_2),
    (False, 'phyloP100way', "chr1:20003-20004", phylo_chr1_2),
    (True, 'phastCons100way', "chr2:20003-20004", phast_chr2_2),
    (False, 'phastCons100way', "chr2:20003-20004", phast_chr2_2),
    (True, 'phyloP100way', "chr2:20003-20004", phylo_chr2_2),
    (False, 'phyloP100way', "chr2:20003-20004", phylo_chr2_2),
])
def test_regions_parameterized(
        expected_df, variants_io, capsys,
        direct, score_name, region, expected):

    score_filename = \
        "fixtures/TEST3{score_name}/TEST3{score_name}.bedGraph.gz".\
        format(score_name=score_name)

    options = Box({
        'mode': 'replace',
        "vcf": True,
        "Graw": "fake_genome_ref_file",
        "direct": direct,
        "region": region,
        "scores_file": relative_to_this_test_folder(score_filename)
    }, default_box=True, default_box_attr=None)

    columns_config = {
        'TEST{}'.format(score_name): "RESULT_{}".format(score_name),
    }

    config = VariantAnnotatorConfig(
        name="test_annotator",
        annotator_name="score_annotator.VariantScoreAnnotator",
        options=options,
        columns_config=columns_config,
        virtuals=[]
    )

    with variants_io("fixtures/input3.tsv.gz", options) as io_manager:
        score_annotator = PositionScoreAnnotator(config)
        assert score_annotator is not None

        captured = capsys.readouterr()

        score_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)
    pd.testing.assert_frame_equal(
        expected_df(captured.out),
        expected_df(expected),
        check_less_precise=3)


missing_phast_chr2_2 = """CHROM	POS	REF	ALT	RESULT_phastCons100way
chr2	20006	G	T
chr2	20007	G	A
"""

missing_phylo_chr2_2 = """CHROM	POS	REF	ALT	RESULT_phyloP100way
chr2	20003	G	T	-100
chr2	20004	G	A	-100
"""

missing_phast_chr22_2 = """CHROM	POS	REF	ALT	RESULT_phastCons100way
"""


@pytest.mark.parametrize("direct,score_name,region,expected", [
    (True, 'phastCons100way', "chr2:20006-20007", missing_phast_chr2_2),
    (False, 'phastCons100way', "chr2:20006-20007", missing_phast_chr2_2),
    (True, 'phyloP100way', "chr2:20003-20004", missing_phylo_chr2_2),
    (False, 'phyloP100way', "chr2:20003-20004", missing_phylo_chr2_2),
    (True, 'phastCons100way', "chr22:20006-20007", missing_phast_chr22_2),
    (False, 'phastCons100way', "chr22:20006-20007", missing_phast_chr22_2),
])
def test_regions_parameterized_missing_scores(
        expected_df, variants_io, capsys,
        direct, score_name, region, expected):

    score_filename = \
        "fixtures/TEST{score_name}/TEST{score_name}.bedGraph.gz".\
        format(score_name=score_name)

    options = Box({
        'mode': 'replace',
        "vcf": True,
        "Graw": "fake_genome_ref_file",
        "direct": direct,
        "region": region,
        "scores_file": relative_to_this_test_folder(score_filename)
    }, default_box=True, default_box_attr=None)

    columns_config = {
        'TEST{}'.format(score_name): "RESULT_{}".format(score_name),
    }

    config = VariantAnnotatorConfig(
        name="test_annotator",
        annotator_name="score_annotator.VariantScoreAnnotator",
        options=options,
        columns_config=columns_config,
        virtuals=[]
    )

    with variants_io("fixtures/input3.tsv.gz", options) as io_manager:
        score_annotator = PositionScoreAnnotator(config)
        assert score_annotator is not None

        captured = capsys.readouterr()

        score_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)
    pd.testing.assert_frame_equal(
        expected_df(captured.out),
        expected_df(expected),
        check_less_precise=3,
        check_dtype=False)


def test_regions_simple(
        expected_df, variants_io, capsys):

    direct = True
    score_name = 'phastCons100way'
    region = "chr1:20003-20004"
    expected = phast_chr1_2

    score_filename = \
        "fixtures/TEST3{score_name}/TEST3{score_name}.bedGraph.gz".\
        format(score_name=score_name)

    options = Box({
        'mode': 'replace',
        "vcf": True,
        "Graw": "fake_genome_ref_file",
        "direct": direct,
        "region": region,
        "scores_file": relative_to_this_test_folder(score_filename)
    }, default_box=True, default_box_attr=None)

    columns_config = {
        'TEST{}'.format(score_name): "RESULT_{}".format(score_name),
    }

    config = VariantAnnotatorConfig(
        name="test_annotator",
        annotator_name="score_annotator.VariantScoreAnnotator",
        options=options,
        columns_config=columns_config,
        virtuals=[]
    )

    with variants_io("fixtures/input3.tsv.gz", options) as io_manager:
        score_annotator = PositionScoreAnnotator(config)
        assert score_annotator is not None

        captured = capsys.readouterr()

        score_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)
    pd.testing.assert_frame_equal(
        expected_df(captured.out),
        expected_df(expected),
        check_less_precise=3)
