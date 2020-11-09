import pytest
import pandas as pd

from dae.annotation.annotation_pipeline import PipelineAnnotator
from dae.annotation.tools.annotator_base import VariantAnnotatorBase

from .conftest import relative_to_this_test_folder


input2_copy_expected = """chr\tposition
1\t10918
1\t10919
1\t10920
1\t10921
1\t10922
"""

input2_score_expected = """RESULT_phastCons100way\tloc1\tvar1
0.253\t1:10918\tsub(G->A)
0.251\t1:10919\tsub(A->C)
0.249\t1:10920\tsub(G->T)
0.247\t1:10921\tsub(A->C)
0.245\t1:10922\tsub(G->C)
"""

input2_score2_expected = """loc1\tvar1\tRESULT_phastCons100way\tRESULT_RawScore\tRESULT_PHRED
1:10918\tsub(G->A)\t0.253\t0.40161\t6.631
1:10919\tsub(A->C)\t0.251\t0.537788\t7.986
1:10920\tsub(G->T)\t0.249\t0.371362\t6.298
1:10921\tsub(A->C)\t0.247\t0.537794\t7.986
1:10922\tsub(G->C)\t0.245\t0.391539\t6.522
"""


@pytest.mark.parametrize(
    "config_file,expected",
    [
        ("fixtures/copy_annotator.conf", input2_copy_expected),
        ("fixtures/score_annotator.conf", input2_score_expected),
        ("fixtures/score2_annotator.conf", input2_score2_expected),
    ],
)
def test_build_pipeline(
    expected_df, variants_io, capsys, config_file, expected, genomes_db_2013
):

    options = {
        "vcf": True,
        "mode": "overwrite",
    }

    filename = relative_to_this_test_folder(config_file)

    captured = capsys.readouterr()
    with variants_io("fixtures/input2.tsv") as io_manager:
        pipeline = PipelineAnnotator.build(options, filename, genomes_db_2013,)
        assert pipeline is not None
        pipeline.annotate_file(io_manager)
    captured = capsys.readouterr()

    print(captured.err)
    print(captured.out)

    cap_df = expected_df(captured.out)

    pd.testing.assert_frame_equal(
        cap_df, expected_df(expected),
        rtol=10e-3,
        check_names=False
    )


def dummy_variant_annotate(annotator, aline, variant, liftover_variants):
    aline["changed_chrom"] = "test"
    aline["changed_position"] = 42


@pytest.fixture(autouse=True)
def mock(mocker):
    mocker.patch.object(
        VariantAnnotatorBase, "do_annotate", new=dummy_variant_annotate
    )


expected_change_variants_position = (
    """test_copy_chr	test_copy_pos	test_vcf_chr	"""
    """test_vcf_pos	test_cshl_chr	test_cshl_pos
test	42	test	42	test	42
test	42	test	42	test	42
test	42	test	42	test	42
test	42	test	42	test	42
test	42	test	42	test	42
"""
)


def test_pipeline_change_variants_position(
    variants_io, capsys, expected_df, genomes_db_2013
):

    options = {
        "default_arguments": None,
        "vcf": True,
        "mode": "overwrite",
    }

    filename = relative_to_this_test_folder(
        "fixtures/variant_coordinates_change.conf"
    )

    with variants_io("fixtures/input2.tsv") as io_manager:
        pipeline = PipelineAnnotator.build(options, filename, genomes_db_2013,)
        assert pipeline is not None

        pipeline.annotate_file(io_manager)
    captured = capsys.readouterr()

    print(captured.err)
    print(captured.out)

    pd.testing.assert_frame_equal(
        expected_df(captured.out),
        expected_df(expected_change_variants_position),
        rtol=10e-3,
        check_names=False,
    )
