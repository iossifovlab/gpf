import pytest
import pandas as pd

from collections import OrderedDict

from .conftest import relative_to_this_test_folder

from dae.annotation.tools.annotator_config import AnnotationConfigParser
from dae.annotation.tools.score_annotator import (
    NPScoreAnnotator,
    PositionScoreAnnotator,
)


indels1_cadd_expected = """
CHROM	POS	REF	ALT	RESULT_RawScore	RESULT_PHRED
chr1	20000	T	G	0.376652\t6.357
chr1	20001	CCT	C	0.26309\t4.8102
chr2	20000	T	G	-0.2072\t0.323
chr2	20001	GGG	G	-0.07853\t0.9539
chr3	20000	A	G	-0.2746\t0.184
chr3	20001	ATT	A	0.01407\t1.8597
"""
indels2_cadd_expected = """CHROM	POS	REF	ALT	RESULT_RawScore	RESULT_PHRED
chr1	20000	T	A	0.3512	6.067
chr1	20001	C	CGGG	0.3337	5.7259
chr2	20000	T	A	-0.2327	0.262
chr2	20001	G	GCCC	-0.03689	1.1575
chr3	20000	A	C	-0.2950	0.154
chr3	20001	A	ACCC	-0.0988	0.8059
"""


@pytest.mark.parametrize(
    "direct,infile,expected",
    [
        (True, "fixtures/indels1.tsv", indels1_cadd_expected),
        (False, "fixtures/indels1.tsv", indels1_cadd_expected),
        (True, "fixtures/indels2.tsv", indels2_cadd_expected),
        (False, "fixtures/indels2.tsv", indels2_cadd_expected),
    ],
)
def test_np_score_annotator_indels(
    expected_df, variants_io, capsys, genomes_db_2013, direct, infile, expected
):

    score_filename = "fixtures/TEST3CADD/TEST3whole_genome_SNVs.tsv.gz"

    options = {
        "mode": "replace",
        "vcf": True,
        "direct": direct,
        "region": None,
        "scores_file": relative_to_this_test_folder(score_filename),
    }

    columns = OrderedDict(
        [("RawScore", "RESULT_RawScore"), ("PHRED", "RESULT_PHRED")]
    )

    config = AnnotationConfigParser.parse_section({
            "options": options,
            "columns": columns,
            "annotator": "score_annotator.NPScoreAnnotator",
            "virtual_columns": [],
        }
    )

    with variants_io(infile, options) as io_manager:
        score_annotator = NPScoreAnnotator(config, genomes_db_2013)
        assert score_annotator is not None

        captured = capsys.readouterr()

        score_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)
    pd.testing.assert_frame_equal(
        expected_df(captured.out),
        expected_df(expected),
        rtol=10e-3,
        check_names=False,
    )


indels1_phylo_expected = """CHROM	POS	REF	ALT	RESULT_phyloP100way
chr1	20000	T	G	0.25
chr1	20001	CCT	C	0.4165
chr2	20000	T	G	-0.86
chr2	20001	GGG	G	0.65375
chr3	20000	A	G	0.024
chr3	20001	ATT	A	-0.06275
"""
indels2_phylo_expected = """CHROM	POS	REF	ALT	RESULT_phyloP100way
chr1	20000	T	A	0.25
chr1	20001	C	CGGG	0.8395
chr2	20000	T	A	-0.86
chr2	20001	G	GCCC	0.7625
chr3	20000	A	C	0.024
chr3	20001	A	ACCC	-0.254
"""


@pytest.mark.parametrize(
    "direct,infile,expected",
    [
        (True, "fixtures/indels1.tsv", indels1_phylo_expected),
        (False, "fixtures/indels1.tsv", indels1_phylo_expected),
        (True, "fixtures/indels2.tsv", indels2_phylo_expected),
        (False, "fixtures/indels2.tsv", indels2_phylo_expected),
    ],
)
def test_position_score_annotator_indels(
    expected_df, variants_io, capsys, genomes_db_2013, direct, infile, expected
):

    score_filename = "fixtures/TEST3phyloP100way/TEST3phyloP100way.bedGraph.gz"

    options = {
        "mode": "replace",
        "vcf": True,
        "direct": direct,
        "region": None,
        "scores_file": relative_to_this_test_folder(score_filename),
    }

    columns = {
        "TESTphyloP100way": "RESULT_phyloP100way",
    }

    config = AnnotationConfigParser.parse_section({
            "options": options,
            "columns": columns,
            "annotator": "score_annotator.NPScoreAnnotator",
            "virtual_columns": [],
        }
    )

    with variants_io(infile, options) as io_manager:
        score_annotator = PositionScoreAnnotator(config, genomes_db_2013)
        assert score_annotator is not None

        captured = capsys.readouterr()

        score_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)
    pd.testing.assert_frame_equal(
        expected_df(captured.out),
        expected_df(expected),
        rtol=10e-3,
        check_names=False,
    )


@pytest.mark.parametrize(
    "chrom,pos,ref,alt,t1,t2,t3",
    [
        ("1", 10000, "C", "A", -100, -100, -100),
        ("1", 10914, "C", "A", 1, 1, 1),
        ("1", 10914, "C", "CA", 3, 1.5, 4.5),
        ("1", 10914, "C", "CAA", 3, 1.5, 4.5),
        ("1", 10914, "CG", "C", 3, 2, 6),
        ("1", 10914, "CGC", "C", 3, 2.5, 7.5),
        ("1", 10914, "CGC", "CA", 3, 2.5, 7.5),
        ("1", 10914, "CGC", "CAA", 3, 2.5, 7.5),
    ],
)
def test_np_score_annotator_indels_test_score(
    chrom, pos, ref, alt, t1, t2, t3, genomes_db_2013
):

    score_filename = "fixtures/TESTCADD/TESTwhole_genome_SNVs.tsv.gz"

    options = {
        "mode": "replace",
        "vcf": True,
        "direct": False,
        "region": None,
        "scores_file": relative_to_this_test_folder(score_filename),
    }

    columns = OrderedDict(
        [("TEST", "TEST"), ("TEST2", "TEST2"), ("TEST3", "TEST3")]
    )

    config = AnnotationConfigParser.parse_section({
            "options": options,
            "columns": columns,
            "annotator": "score_annotator.PositionScoreAnnotator",
            "virtual_columns": [],
        }
    )

    score_annotator = NPScoreAnnotator(config, genomes_db_2013)
    assert score_annotator is not None

    line = {"CHROM": chrom, "POS": pos, "REF": ref, "ALT": alt}
    score_annotator.line_annotation(line)
    assert float(line["TEST"]) == pytest.approx(t1, 1e-4)
    assert float(line["TEST2"]) == pytest.approx(t2, 1e-4)
    assert float(line["TEST3"]) == pytest.approx(t3, 1e-4)


@pytest.mark.parametrize(
    "chrom,pos,ref,alt,t1,t2,t3",
    [
        ("1", 10917, "A", "T", -100, -100, -100),
        ("1", 10918, "G", "A", 1, 1, 1),
        ("1", 10918, "G", "CA", 1, 1.5, 5.5),
        ("1", 10918, "G", "CA", 1, 1.5, 5.5),
        ("1", 10918, "GA", "C", 1, 2, 4),
        ("1", 10918, "GAG", "C", 1, 2.5, 5.5),
        ("1", 10918, "GAG", "CA", 1, 2.5, 5.5),
        ("1", 10918, "GAG", "CAA", 1, 2.5, 5.5),
    ],
)
def test_position_score_annotator_indels_test_score(
    chrom, pos, ref, alt, t1, t2, t3, genomes_db_2013
):

    score_filename = "fixtures/TESTphyloP100way/TESTphyloP100way.bedGraph.gz"

    options = {
        "mode": "replace",
        "vcf": True,
        "direct": False,
        "region": None,
        "scores_file": relative_to_this_test_folder(score_filename),
    }

    columns = OrderedDict(
        [("TEST", "TEST"), ("TEST2", "TEST2"), ("TEST3", "TEST3")]
    )

    config = AnnotationConfigParser.parse_section({
            "options": options,
            "columns": columns,
            "annotator": "score_annotator.PositionScoreAnnotator",
            "virtual_columns": [],
        }
    )

    score_annotator = PositionScoreAnnotator(config, genomes_db_2013)
    assert score_annotator is not None

    line = {"CHROM": chrom, "POS": pos, "REF": ref, "ALT": alt}
    score_annotator.line_annotation(line)
    assert float(line["TEST"]) == pytest.approx(t1, 1e-4)
    assert float(line["TEST2"]) == pytest.approx(t2, 1e-4)
    assert float(line["TEST3"]) == pytest.approx(t3, 1e-4)
