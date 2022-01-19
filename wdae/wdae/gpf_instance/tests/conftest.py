import pytest

from box import Box

from dae.gpf_instance.gpf_instance import cached
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.group_repository import GenomicResourceGroupRepo
from dae.genomic_resources.gene_models_resource import \
    load_gene_models_from_resource

from gpf_instance.gpf_instance import WGPFInstance


@pytest.fixture(scope="session")
def wgpf_instance(default_dae_config, fixture_dirname):

    class WGPFInstanceInternal(WGPFInstance):
        @property  # type: ignore
        @cached
        def gene_models(self):
            print(self.dae_config.gene_models)
            resource = self.grr.get_resource(
                "hg19/gene_models/refGene_v201309")
            gene_models = load_gene_models_from_resource(resource)
            return gene_models

    def build(work_dir=None, load_eagerly=False):
        result = WGPFInstanceInternal(
            work_dir=work_dir, load_eagerly=load_eagerly)
        repositories = [
            result.grr
        ]
        repositories.append(
                build_genomic_resource_repository(
                    Box({
                        "id": "fixtures",
                        "type": "directory",
                        "directory": f"{fixture_dirname('genomic_resources')}"
                    })))
        result.grr = GenomicResourceGroupRepo(repositories)

        return result

    return build


@pytest.fixture(scope="function")
def wgpf_instance_fixture(
        wgpf_instance, admin_client, remote_settings, global_dae_fixtures_dir):
    return wgpf_instance(global_dae_fixtures_dir)
