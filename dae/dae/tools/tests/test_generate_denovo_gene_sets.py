import pytest

from dae.tools.generate_denovo_gene_sets import main


# pytestmark = pytest.mark.usefixtures("gene_info_cache_dir")


def test_generate_denovo_gene_sets_script_passes(gpf_instance_2013):
    main(gpf_instance=gpf_instance_2013, argv=[])
    main(gpf_instance=gpf_instance_2013, argv=["--show-studies"])
