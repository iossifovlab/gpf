import pytest
from box import Box
from .conftest import relative_to_this_test_folder
from annotation.tools.annotator_config import AnnotatorConfig
from annotation.tools.vcf_info_extractor import VCFInfoExtractor
from annotation.tools.file_io import IOManager, IOType


@pytest.fixture
def vcf_io(request):
    io_config = {
        "infile": relative_to_this_test_folder("fixtures/vcf_input.tsv"),
        "outfile": "-",
    }
    io_config = Box(io_config, default_box=True, default_box_attr=None)
    io_manager = IOManager(io_config, IOType.TSV, IOType.TSV)
    return io_manager


def test_vcf_info_extractor(capsys, vcf_io):

    expected_output = \
        ('extracted-AC\textracted-AB\textracted-AT\textracted-AZ\n'
         '0\t7.324234\t4.453e-10\ttest1\n'
         '2\t\t6.453e+10\ttest2\n'
         '4\t11.324234\t\ttest3\n'
         '\t13.324234\t10.453e+10\t\n')

    opts = Box({
        "mode": "overwrite",
    }, default_box=True, default_box_attr=None)

    section_config = AnnotatorConfig(
        name="vcf info extract test",
        annotator_name="vcf_info_extractor.VCFInfoExtractor",
        options=opts,
        columns_config={
            "AC": "extracted-AC",
            "AB": "extracted-AB",
            "AT": "extracted-AT",
            "AZ": "extracted-AZ"
        },
        virtuals=[]
    )

    with vcf_io as io_manager:
        annotator = VCFInfoExtractor(section_config)
        assert annotator is not None
        capsys.readouterr()
        annotator.annotate_file(io_manager)

    # print(variants_input.output)
    captured = capsys.readouterr()

    print(captured.out)
    print(captured.err)
    print(expected_output)
    assert captured.out == expected_output
#     assert captured.err == "Processed 4 lines.\n"
