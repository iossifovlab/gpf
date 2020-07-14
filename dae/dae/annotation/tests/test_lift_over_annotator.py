import pytest
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.annotation.tools.annotator_config import AnnotationConfigParser
from dae.annotation.tools.lift_over_annotator import LiftOverAnnotator
from dae.annotation.annotation_pipeline import PipelineAnnotator

from .conftest import relative_to_this_test_folder


@pytest.mark.parametrize(
    "chrom,pos,lift_over,expected",
    [
        ("chr1", 10000, lambda c, p: [(c, p + 1000)], "chr1:11000"),
        (
            "chr1",
            10000,
            lambda c, p: [(c, p + 1000), (c, p + 2000)],
            "chr1:11000",
        ),
        ("chr1", 10000, lambda c, p: [], None),
    ],
)
def test_lift_over(mocker, chrom, pos, lift_over, expected, genomes_db_2013):

    options = {
        "mode": "replace",
        "vcf": True,
        "direct": True,
        "region": None,
        "chain_file": "fake_chain_file",
        "c": "chrom",
        "p": "pos",
    }

    columns = {
        "new_x": "hg19_location",
    }

    config = AnnotationConfigParser.parse_section(
        GPFConfigParser._dict_to_namedtuple(
            {
                "options": options,
                "columns": columns,
                "annotator": "lift_over_annotator.LiftOverAnnotator",
                "virtual_columns": [],
            }
        )
    )
    mocker.patch(
        "dae.annotation.tools.lift_over_annotator."
        "LiftOverAnnotator.build_lift_over"
    )

    annotator = LiftOverAnnotator(config, genomes_db_2013)
    assert annotator is not None

    annotator.lift_over = mocker.Mock()
    annotator.lift_over.convert_coordinate = lift_over

    aline = {
        "chrom": chrom,
        "pos": pos,
    }

    annotator.do_annotate(aline, None)

    assert "hg19_location" in aline
    assert aline["hg19_location"] == expected


@pytest.mark.parametrize(
    "location,lift_over,expected_location",
    [
        ("chr1:20000", lambda c, p: [(c, p + 2000)], "chr1:22000"),
        (
            "chr1:20000",
            lambda c, p: [(c, p + 2000), (c, p + 3000)],
            "chr1:22000",
        ),
        ("chr1:20000", lambda c, p: [], None),
    ],
)
def test_pipeline_with_liftover(
    mocker, location, lift_over, expected_location, genomes_db_2013
):

    options = {
        "default_arguments": None,
        "vcf": True,
    }

    filename = relative_to_this_test_folder(
        "fixtures/lift_over_test_annotator.conf"
    )

    mocker.patch(
        "dae.annotation.tools.lift_over_annotator."
        "LiftOverAnnotator.build_lift_over"
    )
    pipeline = PipelineAnnotator.build(options, filename, genomes_db_2013,)
    assert pipeline is not None
    assert len(pipeline.annotators) == 3

    lift_over_annotator = pipeline.annotators[0]
    assert isinstance(lift_over_annotator, LiftOverAnnotator)

    lift_over_annotator.lift_over = mocker.Mock()
    lift_over_annotator.lift_over.convert_coordinate = lift_over

    chrom, pos = location.split(":")
    pos = int(pos)

    aline = {
        # 'location': location,
        "CHROM": chrom,
        "POS": pos,
        "REF": "A",
        "ALT": "T",
    }

    pipeline.line_annotation(aline)
    print(aline)
    assert aline["RESULT_phastCons100way"] is None
    assert aline["RESULT_RawScore"] is None
    assert aline["RESULT_PHRED"] is None
