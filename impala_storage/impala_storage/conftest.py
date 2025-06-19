# pylint: disable=W0621,C0114,C0116,W0212,W0613
import logging
import os
import pathlib
import shutil
import tempfile
from collections.abc import Generator

import pytest
from dae.configuration.gpf_config_parser import (
    DefaultBox,
    FrozenBox,
    GPFConfigParser,
)
from dae.configuration.schemas.dae_conf import dae_conf_schema
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.gene_models import build_gene_models_from_resource
from dae.genomic_resources.group_repository import GenomicResourceGroupRepo
from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource,
)
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

    def builder(  # pylint: disable=W0102
        path,
        params={  # noqa: B006
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


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "tests", path,
    )


@pytest.fixture(scope="session")
def fixture_dirname():
    def builder(relpath):
        return relative_to_this_test_folder(os.path.join("fixtures", relpath))

    return builder


def get_global_dae_fixtures_dir():
    return relative_to_this_test_folder("fixtures")


@pytest.fixture(scope="session")
def global_dae_fixtures_dir():
    return get_global_dae_fixtures_dir()


@pytest.fixture(scope="session")
def default_dae_config(fixture_dirname):
    studies_dirname = tempfile.mkdtemp(prefix="studies_", suffix="_test")
    datasets_dirname = tempfile.mkdtemp(prefix="datasets_", suffix="_test")

    conf_dir = fixture_dirname("")
    assert conf_dir is not None

    dae_conf_path = os.path.join(conf_dir, "gpf_instance.yaml")

    dae_config = GPFConfigParser.parse_and_interpolate_file(dae_conf_path)

    dae_config["studies"]["dir"] = studies_dirname
    dae_config["datasets"]["dir"] = datasets_dirname

    dae_config = GPFConfigParser.process_config(
        dae_config,
        dae_conf_schema,
        conf_dir=conf_dir,
    )
    yield dae_config, dae_conf_path

    shutil.rmtree(studies_dirname)
    shutil.rmtree(datasets_dirname)


@pytest.fixture(scope="session")
def grr_test_repo(fixture_dirname):
    return build_genomic_resource_repository(
        {
            "id": "grr_test_repo",
            "type": "directory",
            "directory": fixture_dirname("test_repo"),
        },
    )


@pytest.fixture(scope="session")
def gpf_instance(default_dae_config, fixture_dirname, grr_test_repo):  # noqa: ARG001
    # pylint: disable=import-outside-toplevel
    from dae.gpf_instance.gpf_instance import GPFInstance

    def build(config_filename):
        repositories = [
            grr_test_repo,
            build_genomic_resource_repository(
                {
                    "id": "fixtures",
                    "type": "directory",
                    "directory": fixture_dirname("genomic_resources"),
                }),
            build_genomic_resource_repository(),
        ]
        grr = GenomicResourceGroupRepo(repositories)

        return GPFInstance.build(config_filename, grr=grr)

    return build


@pytest.fixture(scope="session")
def gpf_instance_2013(
        default_dae_config, fixture_dirname,
        global_dae_fixtures_dir, grr_test_repo):
    # pylint: disable=import-outside-toplevel
    from dae.gpf_instance.gpf_instance import GPFInstance

    dae_config, dae_config_path = default_dae_config

    repositories = [
        grr_test_repo,
        build_genomic_resource_repository({
            "id": "fixtures",
            "type": "directory",
            "directory": fixture_dirname("genomic_resources"),
        }),
        build_genomic_resource_repository(),
    ]
    grr = GenomicResourceGroupRepo(repositories)

    resource = grr.get_resource(
        "hg19/gene_models/refGene_v201309")
    gene_models = build_gene_models_from_resource(resource)
    gene_models.load()

    resource = grr.get_resource(
        "hg19/genomes/GATK_ResourceBundle_5777_b37_phiX174")
    genome = build_reference_genome_from_resource(resource)
    genome.open()

    return GPFInstance(
        dae_config=dae_config,
        dae_dir=global_dae_fixtures_dir,
        dae_config_path=dae_config_path,
        grr=grr, gene_models=gene_models, reference_genome=genome)  # type: ignore


@pytest.fixture
def temp_filename():
    dirname = tempfile.mkdtemp(suffix="_eff", prefix="variants_")

    output = os.path.join(dirname, "temp_filename.tmp")
    yield output

    shutil.rmtree(dirname)


@pytest.fixture
def temp_dirname():
    dirname = tempfile.mkdtemp(suffix="_data", prefix="variants_")
    yield dirname
    shutil.rmtree(dirname)


@pytest.fixture(scope="session")
def fixtures_gpf_instance(gpf_instance, global_dae_fixtures_dir):
    return gpf_instance(
        os.path.join(global_dae_fixtures_dir, "gpf_instance.yaml"))


def from_prefix_vcf(prefix):
    pedigree_filename = f"{prefix}.ped"
    assert os.path.exists(pedigree_filename)
    conf = {
        "prefix": prefix,
        "pedigree": pedigree_filename,
    }

    vcf_filename = f"{prefix}.vcf"
    if not os.path.exists(vcf_filename):
        vcf_filename = f"{prefix}.vcf.gz"
    if os.path.exists(vcf_filename):
        conf["vcf"] = vcf_filename

    denovo_filename = f"{prefix}.tsv"
    if os.path.exists(denovo_filename):
        conf["denovo"] = denovo_filename
    return DefaultBox(conf)


@pytest.fixture(scope="session")
def vcf_loader_data():
    def builder(path):
        if os.path.isabs(path):
            prefix = path
        else:
            prefix = os.path.join(
                relative_to_this_test_folder("fixtures"), path,
            )
        return from_prefix_vcf(prefix)

    return builder


@pytest.fixture(scope="session")
def gpf_instance_2019(
        default_dae_config, fixture_dirname,
        global_dae_fixtures_dir, grr_test_repo):
    # pylint: disable=import-outside-toplevel
    from dae.gpf_instance.gpf_instance import GPFInstance

    dae_config, dae_config_path = default_dae_config

    repositories = [
        grr_test_repo,
        build_genomic_resource_repository({
            "id": "fixtures",
            "type": "directory",
            "directory": fixture_dirname("genomic_resources"),
        }),
        build_genomic_resource_repository(),
    ]
    grr = GenomicResourceGroupRepo(repositories)
    resource = grr.get_resource(
        "hg19/gene_models/refGene_v20190211")
    gene_models = build_gene_models_from_resource(resource)
    gene_models.load()

    resource = grr.get_resource(
        "hg19/genomes/GATK_ResourceBundle_5777_b37_phiX174")
    genome = build_reference_genome_from_resource(resource)
    genome.open()

    return GPFInstance(
        dae_config=dae_config,
        dae_dir=global_dae_fixtures_dir,
        dae_config_path=dae_config_path,
        grr=grr, gene_models=gene_models,  # type: ignore
        reference_genome=genome)  # type: ignore


def from_prefix_dae(prefix):
    summary_filename = f"{prefix}.txt.gz"
    toomany_filename = f"{prefix}-TOOMANY.txt.gz"
    family_filename = f"{prefix}.families.txt"

    conf = {
        "dae": {
            "summary_filename": summary_filename,
            "toomany_filename": toomany_filename,
            "family_filename": family_filename,
        },
    }
    return FrozenBox(conf)


@pytest.fixture
def dae_transmitted_config():
    fullpath = relative_to_this_test_folder(
        "fixtures/dae_transmitted/transmission",
    )
    config = from_prefix_dae(fullpath)
    return config.dae


def from_prefix_denovo(prefix):
    denovo_filename = f"{prefix}.txt"
    family_filename = f"{prefix}_families.ped"

    conf = {
        "prefix": prefix,
        "pedigree": family_filename,
        "denovo": denovo_filename,
    }
    return DefaultBox(conf)


@pytest.fixture
def dae_denovo_config():
    fullpath = relative_to_this_test_folder("fixtures/dae_denovo/denovo")
    return from_prefix_denovo(fullpath)


@pytest.fixture(scope="session")
def annotation_pipeline_no_effects_config():
    return relative_to_this_test_folder(
        "fixtures/annotation_pipeline/import_annotation_no_effects.yaml")


@pytest.fixture(scope="session")
def annotation_scores_dirname():
    return relative_to_this_test_folder("fixtures/annotation_pipeline/")
