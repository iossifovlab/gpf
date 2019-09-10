import pytest

from dae.tools.generate_denovo_gene_sets import main


pytestmark = pytest.mark.usefixtures('gene_info_cache_dir')


def test_generate_denovo_gene_sets_script_passes(dae_config_fixture):
    main(dae_config=dae_config_fixture, argv=[])
    main(dae_config=dae_config_fixture, argv=['--show-studies'])
