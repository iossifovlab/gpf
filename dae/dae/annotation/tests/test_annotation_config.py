from dae.annotation.tests.conftest import relative_to_this_test_folder

from dae.annotation.tools.annotator_config import \
    annotation_config_cli_options, \
    AnnotationConfigParser

from dae_conftests.dae_conftests import get_global_dae_fixtures_dir


def test_annotation_config_cli_options(gpf_instance, work_dir, fixture_dirname):
    cli_options = annotation_config_cli_options(gpf_instance(get_global_dae_fixtures_dir()))

    assert len(cli_options) == 10

    assert cli_options[0][0] == '--annotation'
    assert cli_options[0][1]['default'] == \
        fixture_dirname('annotation_pipeline/import_annotation.conf')

    assert cli_options[-2][0] == '--Graw'
    assert cli_options[-2][1]['default'].endswith(
        'genomes/GATK_ResourceBundle_5777_b37_phiX174/chrAll.fa')

    assert cli_options[-1][0] == '--Traw'
    assert cli_options[-1][1]['default'] == 'RefSeq2013'


def test_annotation_config_options_parsing(gpf_instance_2013):

    annotator_config = \
        AnnotationConfigParser.read_and_parse_file_configuration(
            {},
            relative_to_this_test_folder('fixtures/dummy_annotator.conf'),
            relative_to_this_test_folder(''),
            gpf_instance_2013.genomes_db
        )

    assert annotator_config.sections[0].options.vcf is False
