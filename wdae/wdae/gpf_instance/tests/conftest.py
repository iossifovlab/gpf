import pytest
from dae.genome.genomes_db import GenomesDB
from dae.gpf_instance.gpf_instance import cached
from gpf_instance.gpf_instance import WGPFInstance


@pytest.fixture(scope="session")
def wgpf_instance(default_dae_config):
    class GenomesDbInternal(GenomesDB):
        def get_default_gene_models_id(self, genome_id=None):
            return "RefSeq2013"

    class WGPFInstanceInternal(WGPFInstance):
        pass

    def build(work_dir=None, load_eagerly=False):
        return WGPFInstanceInternal(
            work_dir=work_dir, load_eagerly=load_eagerly)

    return build


@pytest.fixture(scope="function")
def wgpf_instance_fixture(
        wgpf_instance, admin_client, remote_settings, global_dae_fixtures_dir):
    return wgpf_instance(global_dae_fixtures_dir)
