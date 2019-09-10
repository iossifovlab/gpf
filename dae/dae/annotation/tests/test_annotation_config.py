from dae.annotation.tests.conftest import relative_to_this_test_folder

from dae.annotation.tools.annotator_config import annotation_config_cli_options


def test_annotation_config_cli_options(dae_config_fixture):
    cli_options = annotation_config_cli_options(dae_config_fixture)

    assert len(cli_options) == 9

    assert cli_options[0][0] == '--annotation'
    assert cli_options[0][1]['default'] == \
        relative_to_this_test_folder('fixtures/annotation.conf')

    assert cli_options[-1][0] == '--Graw'
    assert cli_options[-1][1]['default'].split('/')[-3:] == \
        ['genomes', 'GATK_ResourceBundle_5777_b37_phiX174', 'chrAll.fa']
