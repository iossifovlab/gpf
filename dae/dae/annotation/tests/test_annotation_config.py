from dae.annotation.tests.conftest import relative_to_this_test_folder

from dae.annotation.tools.annotator_config import (
    annotation_config_cli_options,
    AnnotationConfigParser,
)

# from dae_conftests.dae_conftests import get_global_dae_fixtures_dir


def test_annotation_config_cli_options(
    gpf_instance, work_dir, fixture_dirname
):
    cli_options = annotation_config_cli_options(
        gpf_instance(fixture_dirname("."))
    )

    assert len(cli_options) == 11

    assert cli_options[0][0] == "--annotation"
    assert cli_options[0][1]["default"] == fixture_dirname(
        "annotation_pipeline/import_annotation.conf"
    )

    assert cli_options[-3][0] == "--Graw"
    assert cli_options[-3][1]["default"].endswith(
        "genomes/GATK_ResourceBundle_5777_b37_phiX174/chrAll.fa"
    )

    assert cli_options[-2][0] == "--Traw"
    assert cli_options[-2][1]["default"].endswith(
        "genomes/GATK_ResourceBundle_5777_b37_phiX174/refGene-20190211.gz")


def test_annotation_config_options_parsing(gpf_instance_2013):

    # fmt: off
    annotator_config = AnnotationConfigParser\
        .read_and_parse_file_configuration(
            {}, relative_to_this_test_folder("fixtures/dummy_annotator.conf"),
        )
    # fmt: on
    assert annotator_config.sections[0].options.vcf is False
