import pytest

from tools.generate_denovo_gene_sets import main


pytestmark = pytest.mark.usefixtures('gene_info_cache_dir')


def test_generate_denovo_gene_sets_script_passes():
    main()
