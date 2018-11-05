import pytest
from box import Box
from annotation.tools.annotator_config import VariantAnnotatorConfig
from annotation.tools.lift_over_annotator import LiftOverAnnotator


@pytest.mark.parametrize("location,lift_over,expected", [
    ("chr1:10000", lambda c, p: [(c, p+1000)], "chr1:11000"),
    ("chr1:10000", lambda c, p: [(c, p+1000), (c, p+2000)], "chr1:11000"),
    ("chr1:10000", lambda c, p: [], None),
])
def test_lift_over(mocker, location, lift_over, expected):

    options = Box({
        'mode': 'replace',
        "vcf": True,
        "Graw": "fake_genome_ref_file",
        "direct": True,
        "region": None,
        "chain_file": "fake_chain_file",
        "x": "location",
    }, default_box=True, default_box_attr=None)

    columns = {
        "new_x": "hg19_location",
        # "new_c": "hg19_chr",
        # "new_p": "hg19_pos",
    }

    config = VariantAnnotatorConfig(
        name="Test Lift Over Annotator",
        annotator_name="lift_over_annotator.LiftOverAnnotator",
        options=options,
        columns_config=columns,
        virtuals=[],
    )
    with mocker.patch(
            "annotation.tools.lift_over_annotator."
            "LiftOverAnnotator.build_lift_over"):

        annotator = LiftOverAnnotator(config)
        assert annotator is not None

        annotator.lift_over = mocker.Mock()
        annotator.lift_over.convert_coordinate = lift_over

        aline = {
            'location': location,
        }

        annotator.do_annotate(aline, None)

        assert 'hg19_location' in aline
        assert aline['hg19_location'] == expected
