from dae.annotation.tests.conftest import relative_to_this_test_folder

from dae.annotation.tools.annotator_config import \
    annotation_config_cli_options, \
    AnnotationConfigParser


def test_annotation_config_cli_options(mocked_gpf_instance):
    cli_options = annotation_config_cli_options(mocked_gpf_instance)

    assert len(cli_options) == 10

    assert cli_options[0][0] == '--annotation'
    assert cli_options[0][1]['default'] == \
        relative_to_this_test_folder('fixtures/annotation.conf')

    assert cli_options[-2][0] == '--Graw'
    assert cli_options[-2][1]['default'] == \
        './genomes/GATK_ResourceBundle_5777_b37_phiX174/chrAll.fa'

    assert cli_options[-1][0] == '--Traw'
    assert cli_options[-1][1]['default'] == 'RefSeq2013'


def test_annotation_config_options_parsing(mocked_gpf_instance):

    annotator_config = \
        AnnotationConfigParser.read_and_parse_file_configuration(
            {},
            relative_to_this_test_folder('fixtures/dummy_annotator.conf'),
            relative_to_this_test_folder(''),
            mocked_gpf_instance.genomes_db
        )

    assert annotator_config.step_sample_annotator.options.vcf is False
