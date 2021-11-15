import pytest
from dae.gpf_instance.gpf_instance import cached
from gpf_instance.gpf_instance import WGPFInstance


@pytest.fixture(scope="session")
def wgpf_instance(default_dae_config):

    class WGPFInstanceInternal(WGPFInstance):
        @property  # type: ignore
        @cached
        def gene_models(self):
            print(self.dae_config.gene_models)
            result = self.grr.get_resource(
                "hg19/GATK_ResourceBundle_5777_b37_phiX174/"
                "gene_models/refGene_v201309")
            result.open()
            return result

    def build(work_dir=None, load_eagerly=False):
        return WGPFInstanceInternal(
            work_dir=work_dir, load_eagerly=load_eagerly)

    return build


@pytest.fixture(scope="function")
def wgpf_instance_fixture(
        wgpf_instance, admin_client, remote_settings, global_dae_fixtures_dir):
    return wgpf_instance(global_dae_fixtures_dir)
