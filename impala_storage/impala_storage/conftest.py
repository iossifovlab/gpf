# pylint: disable=W0621,C0114,C0116,W0212,W0613
import logging
import os
import pathlib
from collections.abc import Generator

import pytest

from dae.genotype_storage.genotype_storage_registry import (
    GenotypeStorage,
    GenotypeStorageRegistry,
)
from dae.import_tools.import_tools import (
    construct_import_annotation_pipeline,
)
from dae.pedigrees.loader import FamiliesLoader
from dae.variants_loaders.dae.loader import DenovoLoader
from dae.variants_loaders.vcf.loader import VcfLoader
from impala_storage.schema1.annotation_decorator import (
    AnnotationPipelineDecorator,
)

logger = logging.getLogger(__name__)

pytest_plugins = ["dae_conftests.dae_conftests"]


@pytest.fixture(scope="module")
def resources_dir(request: pytest.FixtureRequest) -> pathlib.Path:
    resources_path = os.path.join(
        os.path.dirname(os.path.realpath(request.module.__file__)),
        "resources")
    return pathlib.Path(resources_path)


@pytest.fixture(scope="session")
def hdfs_host() -> str:
    return os.environ.get("DAE_HDFS_HOST", "127.0.0.1")


@pytest.fixture(scope="session")
def impala_host() -> str:
    return os.environ.get("DAE_IMPALA_HOST", "127.0.0.1")


@pytest.fixture(scope="session")
def impala_genotype_storage(
    hdfs_host: str,
    impala_host: str,
) -> Generator[GenotypeStorage, None, None]:

    storage_config = {
        "id": "impala_test_storage",
        "storage_type": "impala",
        "impala": {
            "hosts": [impala_host],
            "port": 21050,
            "db": "impala_test_db",
            "pool_size": 5,
        },
        "hdfs": {
            "host": hdfs_host,
            "port": 8020,
            "base_dir": "/tmp/test_data",  # noqa: S108
        },
    }
    registry = GenotypeStorageRegistry()
    registry.register_storage_config(storage_config)

    yield registry.get_genotype_storage("impala_test_storage")

    registry.shutdown()


@pytest.fixture(scope="session")
def vcf_variants_loaders(
        vcf_loader_data, gpf_instance_2019):

    annotation_pipeline = construct_import_annotation_pipeline(
        gpf_instance_2019,
    )

    def builder(
        path,
        params={
            "vcf_include_reference_genotypes": True,
            "vcf_include_unknown_family_genotypes": True,
            "vcf_include_unknown_person_genotypes": True,
            "vcf_denovo_mode": "denovo",
            "vcf_omission_mode": "omission",
        },
    ):
        config = vcf_loader_data(path)

        families_loader = FamiliesLoader(config.pedigree)
        families = families_loader.load()

        loaders = []

        if config.denovo:
            denovo_loader = DenovoLoader(
                families,
                config.denovo,
                gpf_instance_2019.reference_genome,
                params={
                    "denovo_genotype": "genotype",
                    "denovo_family_id": "family",
                    "denovo_chrom": "chrom",
                    "denovo_pos": "pos",
                    "denovo_ref": "ref",
                    "denovo_alt": "alt",
                },
            )
            loaders.append(AnnotationPipelineDecorator(
                denovo_loader, annotation_pipeline))

        vcf_loader = VcfLoader(
            families,
            [config.vcf],
            gpf_instance_2019.reference_genome,
            params=params,
        )

        loaders.append(AnnotationPipelineDecorator(
            vcf_loader, annotation_pipeline,
        ))

        return loaders

    return builder
