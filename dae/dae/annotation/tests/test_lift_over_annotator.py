import pytest

from dae.variants.variant import SummaryAllele
# from dae.annotation.tools.annotator_config import AnnotationConfigParser
# from dae.annotation.tools.lift_over_annotator import LiftOverAnnotator
# from dae.annotation.annotation_pipeline import PipelineAnnotator

# from .conftest import relative_to_this_test_folder


# def mock_get_sequence(chrom, start, stop):
#     return "G" * (stop - start + 1)


# @pytest.mark.parametrize(
#     "chrom,pos,lift_over,expected",
#     [
#         (
#             "chr1",
#             10000,
#             lambda c, p: [(c, p + 1000, "+", "")],
#             "chr1:11000"
#         ),
#         (
#             "chr1",
#             10000,
#             lambda c, p: [(c, p + 1000, "+", ""), (c, p + 2000, "+", "")],
#             "chr1:11000",
#         ),
#         (
#             "chr1",
#             10000,
#             lambda c, p: None,
#             None
#         ),
#         (
#             "chr1",
#             10000,
#             lambda c, p: [(c, p + 1000, "-", "")],
#             "chr1:11000"
#         ),
#     ],
# )
# def test_lift_over(mocker, chrom, pos, lift_over, expected, genomes_db_2013):

#     options = {
#         "mode": "replace",
#         "vcf": True,
#         "direct": True,
#         "region": None,
#         "chain_file": "fake_chain_file",
#         "c": "chrom",
#         "p": "pos",
#         "liftover": "lo1",
#     }

#     columns = {
#         "new_x": "hg19_location",
#     }

#     config = AnnotationConfigParser.parse_section({
#             "options": options,
#             "columns": columns,
#             "annotator": "lift_over_annotator.LiftOverAnnotator",
#             "virtual_columns": [],
#         }
#     )
#     mocker.patch(
#         "dae.annotation.tools.lift_over_annotator."
#         "LiftOverAnnotator.load_liftover_chain")

#     mocker.patch(
#         "dae.annotation.tools.lift_over_annotator."
#         "LiftOverAnnotator.load_target_genome")

#     annotator = LiftOverAnnotator(config, genomes_db_2013)
#     assert annotator is not None

#     annotator.liftover = mocker.Mock()
#     annotator.liftover.convert_coordinate = lift_over
#     annotator.target_genome = mocker.Mock()
#     annotator.target_genome.get_sequence = mock_get_sequence

#     aline = {
#         "chrom": chrom,
#         "pos": pos,
#     }
#     allele = SummaryAllele(chrom, pos, "A", "T")
#     liftover_variants = {}
#     annotator.do_annotate(aline, allele, liftover_variants)

#     lo_variant = liftover_variants.get("lo1")
#     print(f"liftover variant: {lo_variant}")
#     lo_location = lo_variant.details.cshl_location if lo_variant else None

#     assert expected == lo_location


# @pytest.mark.parametrize(
#     "location,lift_over,expected_location",
#     [
#         ("chr1:20000", lambda c, p: [(c, p + 2000, "+", "")], "chr1:22000"),
#         (
#             "chr1:20000",
#             lambda c, p: [(c, p + 2000, "+", ""), (c, p + 3000, "+", "")],
#             "chr1:22000",
#         ),
#         ("chr1:20000", lambda c, p: [], None),
#     ],
# )
# def test_pipeline_with_liftover(
#         mocker, location, lift_over, expected_location, genomes_db_2013):

#     options = {
#         "default_arguments": None,
#         "vcf": True,
#     }

#     filename = relative_to_this_test_folder(
#         "fixtures/lift_over_test_annotator.conf"
#     )

#     mocker.patch(
#         "dae.annotation.tools.lift_over_annotator."
#         "LiftOverAnnotator.load_liftover_chain")
#     mocker.patch(
#         "dae.annotation.tools.lift_over_annotator."
#         "LiftOverAnnotator.load_target_genome")

#     pipeline = PipelineAnnotator.build(options, filename, genomes_db_2013,)
#     assert pipeline is not None
#     assert len(pipeline.annotators) == 3

#     lift_over_annotator = pipeline.annotators[0]
#     assert isinstance(lift_over_annotator, LiftOverAnnotator)

#     lift_over_annotator.liftover = mocker.Mock()
#     lift_over_annotator.liftover.convert_coordinate = lift_over
#     lift_over_annotator.target_genome = mocker.Mock()
#     lift_over_annotator.target_genome.get_sequence = mock_get_sequence

#     chrom, pos = location.split(":")
#     pos = int(pos)

#     aline = {
#         # 'location': location,
#         "CHROM": chrom,
#         "POS": pos,
#         "REF": "A",
#         "ALT": "T",
#     }

#     pipeline.line_annotation(aline)

#     assert aline["RESULT_phastCons100way"] is None
#     assert aline["RESULT_RawScore"] is None
#     assert aline["RESULT_PHRED"] is None
