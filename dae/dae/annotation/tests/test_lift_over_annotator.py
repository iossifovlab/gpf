import pytest
from box import Box
from dae.annotation.tools.annotator_config import AnnotationConfigParser
from dae.annotation.tools.lift_over_annotator import LiftOverAnnotator
from dae.annotation.annotation_pipeline import PipelineAnnotator

from .conftest import relative_to_this_test_folder


@pytest.mark.parametrize("chrom,pos,lift_over,expected", [
    ("chr1", 10000, lambda c, p: [(c, p+1000)], "chr1:11000"),
    ("chr1", 10000, lambda c, p: [(c, p+1000), (c, p+2000)], "chr1:11000"),
    ("chr1", 10000, lambda c, p: [], None),
])
def test_lift_over(mocker, chrom, pos, lift_over, expected):

    options = Box({
        'mode': 'replace',
        "vcf": True,
        "Graw": "fake_genome_ref_file",
        "direct": True,
        "region": None,
        "chain_file": "fake_chain_file",
        "c": "chrom",
        "p": "pos",
    }, default_box=True, default_box_attr=None)

    columns = {
        "new_x": "hg19_location",
        # "new_c": "hg19_chr",
        # "new_p": "hg19_pos",
    }

    config = AnnotationConfigParser.parse_section(
        Box({
            'options': options,
            'columns': columns,
            'annotator': 'lift_over_annotator.LiftOverAnnotator'
        })
    )
    with mocker.patch(
            "dae.annotation.tools.lift_over_annotator."
            "LiftOverAnnotator.build_lift_over"):

        annotator = LiftOverAnnotator(config)
        assert annotator is not None

        annotator.lift_over = mocker.Mock()
        annotator.lift_over.convert_coordinate = lift_over

        aline = {
            'chrom': chrom,
            'pos': pos,
        }

        annotator.do_annotate(aline, None)

        assert 'hg19_location' in aline
        assert aline['hg19_location'] == expected


@pytest.mark.parametrize("location,lift_over,expected_location", [
    ("chr1:20000", lambda c, p: [(c, p+2000)], "chr1:22000"),
    ("chr1:20000", lambda c, p: [(c, p+2000), (c, p+3000)], "chr1:22000"),
    ("chr1:20000", lambda c, p: [], None),
])
def test_pipeline_with_liftover(
        mocker, location, lift_over, expected_location):

    options = Box({
            "default_arguments": None,
            "vcf": True,
        },
        default_box=True,
        default_box_attr=None)

    filename = relative_to_this_test_folder(
        "fixtures/lift_over_test_annotator.conf")

    with mocker.patch(
            "dae.annotation.tools.lift_over_annotator."
            "LiftOverAnnotator.build_lift_over"):
        work_dir = relative_to_this_test_folder("fixtures/")

        pipeline = PipelineAnnotator.build(
            options, filename, work_dir,
            defaults={'values': {"fixtures_dir": work_dir}}
        )
        assert pipeline is not None
        assert len(pipeline.annotators) == 3

        lift_over_annotator = pipeline.annotators[0]
        assert isinstance(lift_over_annotator, LiftOverAnnotator)

        lift_over_annotator.lift_over = mocker.Mock()
        lift_over_annotator.lift_over.convert_coordinate = lift_over

        chrom, pos = location.split(':')
        pos = int(pos)

        aline = {
            # 'location': location,
            'CHROM': chrom,
            'POS': pos,
            'REF': 'A',
            'ALT': 'T',
        }

        pipeline.line_annotation(aline)
        print(aline)
        assert aline['RESULT_phastCons100way'] is None
        assert aline['RESULT_RawScore'] is None
        assert aline['RESULT_PHRED'] is None
