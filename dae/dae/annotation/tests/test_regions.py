import pytest
import pandas as pd


# from .conftest import relative_to_this_test_folder

# from dae.annotation.tools.annotator_config import AnnotationConfigParser
# from dae.annotation.tools.score_annotator import PositionScoreAnnotator


# phast_chr1_2 = """CHROM	POS	REF	ALT	RESULT_phastCons100way
# chr1	20003	T	A	0.001
# chr1	20004	G	A	0.0
# """

# phylo_chr1_2 = """CHROM	POS	REF	ALT	RESULT_phyloP100way
# chr1	20003	T	A	0.023
# chr1	20004	G	A	-0.036
# """

# phast_chr2_2 = """CHROM	POS	REF	ALT	RESULT_phastCons100way
# chr2	20003	G	T	0.011
# chr2	20004	G	A	0.004
# """

# phylo_chr2_2 = """CHROM	POS	REF	ALT	RESULT_phyloP100way
# chr2	20003	G	T	1.208
# chr2	20004	G	A	-0.118
# """


# @pytest.mark.parametrize(
#     "direct,score_name,region,expected",
#     [
#         (True, "phastCons100way", "chr1:20003-20004", phast_chr1_2),
#         (False, "phastCons100way", "chr1:20003-20004", phast_chr1_2),
#         (True, "phyloP100way", "chr1:20003-20004", phylo_chr1_2),
#         (False, "phyloP100way", "chr1:20003-20004", phylo_chr1_2),
#         (True, "phastCons100way", "chr2:20003-20004", phast_chr2_2),
#         (False, "phastCons100way", "chr2:20003-20004", phast_chr2_2),
#         (True, "phyloP100way", "chr2:20003-20004", phylo_chr2_2),
#         (False, "phyloP100way", "chr2:20003-20004", phylo_chr2_2),
#     ],
# )
# def test_regions_parameterized(
#         expected_df,
#         variants_io,
#         capsys,
#         genomes_db_2013,
#         direct,
#         score_name,
#         region,
#         expected):

#     score_filename = (
#         f"fixtures/TEST3{score_name}/TEST3{score_name}.bedGraph.gz"
#     )

#     options = {
#         "mode": "replace",
#         "vcf": True,
#         "direct": direct,
#         "region": region,
#         "scores_file": relative_to_this_test_folder(score_filename),
#     }

#     columns = {
#         "TEST{}".format(score_name): "RESULT_{}".format(score_name),
#     }

#     config = AnnotationConfigParser.parse_section({
#             "options": options,
#             "columns": columns,
#             "annotator": "score_annotator.PositionScoreAnnotator",
#             "virtual_columns": [],
#         }
#     )

#     with variants_io("fixtures/input3.tsv.gz", config.options) as io_manager:
#         score_annotator = PositionScoreAnnotator(config, genomes_db_2013)
#         assert score_annotator is not None

#         captured = capsys.readouterr()

#         score_annotator.annotate_file(io_manager)

#     captured = capsys.readouterr()
#     print(captured.err)
#     print(captured.out)
#     pd.testing.assert_frame_equal(
#         expected_df(captured.out), expected_df(expected), rtol=10e-3
#     )


# missing_phast_chr2_2 = """CHROM	POS	REF	ALT	RESULT_phastCons100way
# chr2	20006	G	T
# chr2	20007	G	A
# """

# missing_phylo_chr2_2 = """CHROM	POS	REF	ALT	RESULT_phyloP100way
# chr2	20003	G	T	-100
# chr2	20004	G	A	-100
# """

# missing_phast_chr22_2 = """CHROM	POS	REF	ALT	RESULT_phastCons100way
# """


# @pytest.mark.parametrize(
#     "direct,score_name,region,expected",
#     [
#         (True, "phastCons100way", "chr2:20006-20007", missing_phast_chr2_2),
#         (False, "phastCons100way", "chr2:20006-20007", missing_phast_chr2_2),
#         (True, "phyloP100way", "chr2:20003-20004", missing_phylo_chr2_2),
#         (False, "phyloP100way", "chr2:20003-20004", missing_phylo_chr2_2),
#         (True, "phastCons100way", "chr22:20006-20007", missing_phast_chr22_2),
#         (False, "phastCons100way", "chr22:20006-20007", missing_phast_chr22_2),
#     ],
# )
# def test_regions_parameterized_missing_scores(
#     expected_df,
#     variants_io,
#     capsys,
#     genomes_db_2013,
#     direct,
#     score_name,
#     region,
#     expected,
# ):

#     score_filename = f"fixtures/TEST{score_name}/TEST{score_name}.bedGraph.gz"

#     options = {
#         "mode": "replace",
#         "vcf": True,
#         "direct": direct,
#         "region": region,
#         "scores_file": relative_to_this_test_folder(score_filename),
#     }

#     columns = {
#         "TEST{}".format(score_name): "RESULT_{}".format(score_name),
#     }

#     config = AnnotationConfigParser.parse_section({
#             "options": options,
#             "columns": columns,
#             "annotator": "score_annotator.VariantScoreAnnotator",
#             "virtual_columns": [],
#         }
#     )

#     with variants_io("fixtures/input3.tsv.gz", config.options) as io_manager:
#         score_annotator = PositionScoreAnnotator(config, genomes_db_2013)
#         assert score_annotator is not None

#         captured = capsys.readouterr()

#         score_annotator.annotate_file(io_manager)

#     captured = capsys.readouterr()
#     print(captured.err)
#     print(captured.out)
#     pd.testing.assert_frame_equal(
#         expected_df(captured.out),
#         expected_df(expected),
#         rtol=10e-3,
#         check_dtype=False,
#     )


# def test_regions_simple(expected_df, variants_io, capsys, genomes_db_2013):

#     direct = True
#     score_name = "phastCons100way"
#     region = "chr1:20003-20004"
#     expected = phast_chr1_2

#     score_filename = (
#         f"fixtures/TEST3{score_name}/TEST3{score_name}.bedGraph.gz"
#     )

#     options = {
#         "mode": "replace",
#         "vcf": True,
#         "direct": direct,
#         "region": region,
#         "scores_file": relative_to_this_test_folder(score_filename),
#     }

#     columns = {
#         f"TEST{score_name}": f"RESULT_{score_name}",
#     }

#     config = AnnotationConfigParser.parse_section({
#             "options": options,
#             "columns": columns,
#             "annotator": "score_annotator.VariantScoreAnnotator",
#             "virtual_columns": [],
#         }
#     )

#     with variants_io("fixtures/input3.tsv.gz", config.options) as io_manager:
#         score_annotator = PositionScoreAnnotator(config, genomes_db_2013)
#         assert score_annotator is not None

#         captured = capsys.readouterr()

#         score_annotator.annotate_file(io_manager)

#     captured = capsys.readouterr()
#     print(captured.err)
#     print(captured.out)
#     pd.testing.assert_frame_equal(
#         expected_df(captured.out), expected_df(expected), rtol=10e-3
#     )
