# pylint: disable=W0621,C0114,C0116,C0415,W0212,W0613,C0302,C0115,W0102,W0603

import glob
import logging
import os
import shutil
import sys
import tempfile
from io import StringIO
from pathlib import Path

import pandas as pd
import pytest

from dae.annotation.annotation_factory import load_pipeline_from_file
from dae.configuration.gpf_config_parser import (
    DefaultBox,
    FrozenBox,
    GPFConfigParser,
)
from dae.configuration.schemas.dae_conf import dae_conf_schema
from dae.gene_sets.denovo_gene_set_helpers import (
    DenovoGeneSetHelpers,
)
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.gene_models import build_gene_models_from_resource
from dae.genomic_resources.group_repository import GenomicResourceGroupRepo
from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource,
)
from dae.import_tools.import_tools import (
    ImportProject,
    construct_import_annotation_pipeline,
)
from dae.inmemory_storage.raw_variants import RawMemoryVariants
from dae.pedigrees.loader import FamiliesLoader
from dae.utils.helpers import study_id_from_path
from dae.variants_loaders.dae.loader import DaeTransmittedLoader, DenovoLoader
from dae.variants_loaders.raw.loader import AnnotationPipelineDecorator
from dae.variants_loaders.vcf.loader import VcfLoader

logger = logging.getLogger(__name__)


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "tests", path,
    )


@pytest.fixture(scope="session")
def fixture_dirname(request):
    def builder(relpath):
        return relative_to_this_test_folder(os.path.join("fixtures", relpath))

    return builder


def get_global_dae_fixtures_dir():
    return relative_to_this_test_folder("fixtures")


@pytest.fixture(scope="session")
def global_dae_fixtures_dir():
    return get_global_dae_fixtures_dir()


@pytest.fixture(scope="module")
def resources_dir(request) -> Path:
    resources_path = os.path.join(
        os.path.dirname(os.path.realpath(request.module.__file__)),
        "resources")
    return Path(resources_path)


@pytest.fixture(scope="session")
def default_dae_config(request, fixture_dirname):
    studies_dirname = tempfile.mkdtemp(prefix="studies_", suffix="_test")
    datasets_dirname = tempfile.mkdtemp(prefix="datasets_", suffix="_test")

    def fin():
        shutil.rmtree(studies_dirname)
        shutil.rmtree(datasets_dirname)

    request.addfinalizer(fin)

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
    return dae_config


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
def gpf_instance(default_dae_config, fixture_dirname, grr_test_repo):
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

        instance = GPFInstance.build(config_filename, grr=grr)

        return instance

    return build


@pytest.fixture(scope="session")
def gpf_instance_2013(
        default_dae_config, fixture_dirname,
        global_dae_fixtures_dir, grr_test_repo):
    from dae.gpf_instance.gpf_instance import GPFInstance

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

    gpf_instance = GPFInstance(
        dae_config=default_dae_config,
        dae_dir=global_dae_fixtures_dir,
        grr=grr, gene_models=gene_models, reference_genome=genome)

    return gpf_instance


@pytest.fixture(scope="session")
def fixtures_gpf_instance(gpf_instance, global_dae_fixtures_dir):
    return gpf_instance(
        os.path.join(global_dae_fixtures_dir, "gpf_instance.yaml"))


@pytest.fixture(scope="session")
def gpf_instance_2019(
        default_dae_config, fixture_dirname,
        global_dae_fixtures_dir, grr_test_repo):
    from dae.gpf_instance.gpf_instance import GPFInstance

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

    gpf_instance = GPFInstance(
        dae_config=default_dae_config,
        dae_dir=global_dae_fixtures_dir,
        grr=grr, gene_models=gene_models, reference_genome=genome)

    return gpf_instance


def _create_gpf_instance(
        gene_model_dir, ref_genome_dir,
        default_dae_config, global_dae_fixtures_dir, fixture_dirname):
    from dae.gpf_instance.gpf_instance import GPFInstance

    repositories = [
        build_genomic_resource_repository({
            "id": "grr_test_repo",
            "type": "directory",
            "directory": fixture_dirname("test_repo"),
        }),
        build_genomic_resource_repository({
            "id": "fixtures",
            "type": "directory",
            "directory": fixture_dirname("genomic_resources"),
        }),
        build_genomic_resource_repository(),
    ]
    grr = GenomicResourceGroupRepo(repositories)
    gene_models = None
    if gene_model_dir is not None:
        resource = grr.get_resource(gene_model_dir)
        gene_models = build_gene_models_from_resource(resource)
        gene_models.load()

    genome = None
    if ref_genome_dir is not None:
        resource = grr.get_resource(ref_genome_dir)
        genome = build_reference_genome_from_resource(resource)
        genome.open()

    instance = GPFInstance(
        dae_config=default_dae_config, dae_dir=global_dae_fixtures_dir,
        grr=grr, gene_models=gene_models, reference_genome=genome,
    )

    return instance


@pytest.fixture(scope="session")
def gpf_instance_short(
        default_dae_config, global_dae_fixtures_dir, fixture_dirname):
    return _create_gpf_instance(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/"
        "gene_models/refGene_201309",
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome",
        default_dae_config, global_dae_fixtures_dir, fixture_dirname,
    )


@pytest.fixture(scope="session")
def gpf_instance_grch38(
        default_dae_config, global_dae_fixtures_dir, fixture_dirname):
    return _create_gpf_instance(
        "hg38/GRCh38-hg38/gene_models/refSeq_20200330",
        "hg38/GRCh38-hg38/genome",
        default_dae_config, global_dae_fixtures_dir, fixture_dirname,
    )


@pytest.fixture()
def result_df():
    def build(data):
        infile = StringIO(str(data))
        df = pd.read_csv(infile, sep="\t")
        return df

    return build


@pytest.fixture()
def temp_dirname(request):
    dirname = tempfile.mkdtemp(suffix="_data", prefix="variants_")

    def fin():
        shutil.rmtree(dirname)

    request.addfinalizer(fin)
    return dirname


@pytest.fixture()
def temp_dirname_grdb(request):
    dirname = tempfile.mkdtemp(suffix="_data", prefix="grdb_")

    def fin():
        shutil.rmtree(dirname)

    request.addfinalizer(fin)
    return dirname


@pytest.fixture()
def temp_filename(request):
    dirname = tempfile.mkdtemp(suffix="_eff", prefix="variants_")

    def fin():
        shutil.rmtree(dirname)

    request.addfinalizer(fin)

    output = os.path.join(dirname, "temp_filename.tmp")
    return output


IMPORT_ANNOTATION_CONFIG = \
    "fixtures/annotation_pipeline/import_annotation.yaml"


@pytest.fixture(scope="session")
def annotation_pipeline_config():
    return relative_to_this_test_folder(IMPORT_ANNOTATION_CONFIG)


@pytest.fixture(scope="session")
def annotation_pipeline_no_effects_config():
    return relative_to_this_test_folder(
        "fixtures/annotation_pipeline/import_annotation_no_effects.yaml")


@pytest.fixture(scope="session")
def annotation_pipeline_default_config(default_dae_config):
    return default_dae_config.annotation.conf_file


@pytest.fixture(scope="session")
def annotation_scores_dirname():
    return relative_to_this_test_folder("fixtures/annotation_pipeline/")


@pytest.fixture()
def annotation_pipeline_vcf(gpf_instance_2013):
    filename = relative_to_this_test_folder(IMPORT_ANNOTATION_CONFIG)
    return load_pipeline_from_file(filename, gpf_instance_2013.grr)


@pytest.fixture()
def annotation_pipeline_internal(gpf_instance_2013):
    filename = relative_to_this_test_folder(IMPORT_ANNOTATION_CONFIG)
    pipeline = load_pipeline_from_file(filename, gpf_instance_2013.grr)
    pipeline.open()
    return pipeline


def from_prefix_denovo(prefix):
    denovo_filename = f"{prefix}.txt"
    family_filename = f"{prefix}_families.ped"

    conf = {
        "prefix": prefix,
        "pedigree": family_filename,
        "denovo": denovo_filename,
    }
    return DefaultBox(conf)


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


@pytest.fixture()
def dae_denovo_config():
    fullpath = relative_to_this_test_folder("fixtures/dae_denovo/denovo")
    config = from_prefix_denovo(fullpath)
    return config


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


@pytest.fixture()
def dae_transmitted_config():
    fullpath = relative_to_this_test_folder(
        "fixtures/dae_transmitted/transmission",
    )
    config = from_prefix_dae(fullpath)
    return config.dae


@pytest.fixture()
def dae_transmitted(
    dae_transmitted_config, gpf_instance_2013, annotation_pipeline_internal,
):

    families = FamiliesLoader.load_simple_families_file(
        dae_transmitted_config.family_filename,
    )

    variants_loader = DaeTransmittedLoader(
        families,
        dae_transmitted_config.summary_filename,
        genome=gpf_instance_2013.reference_genome,
        regions=None,
    )
    return AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal,
    )


@pytest.fixture()
def iossifov2014_loader(
        fixture_dirname,
        gpf_instance_2013, annotation_pipeline_internal):

    family_filename = fixture_dirname(
        "dae_iossifov2014/iossifov2014_families.ped")
    denovo_filename = fixture_dirname(
        "dae_iossifov2014/iossifov2014.txt")

    families_loader = FamiliesLoader(family_filename)
    families = families_loader.load()

    variants_loader = DenovoLoader(
        families, denovo_filename,
        gpf_instance_2013.reference_genome,
    )

    return AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal,
    ), families_loader


@pytest.fixture(scope="session")
def vcf_loader_data():
    def builder(path):
        if os.path.isabs(path):
            prefix = path
        else:
            prefix = os.path.join(
                relative_to_this_test_folder("fixtures"), path,
            )
        conf = from_prefix_vcf(prefix)
        return conf

    return builder


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


@pytest.fixture(scope="session")
def variants_vcf(vcf_variants_loaders):
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

        loaders = vcf_variants_loaders(path, params=params)
        assert len(loaders) > 0
        fvars = RawMemoryVariants(loaders, loaders[0].families)
        return fvars

    return builder


@pytest.fixture(scope="session")
def variants_mem():
    def builder(loader):
        fvars = RawMemoryVariants([loader], loader.families)
        return fvars

    return builder


@pytest.fixture()
def variants_implementations(variants_vcf):
    impls = {"variants_vcf": variants_vcf}
    return impls


@pytest.fixture()
def variants_impl(variants_implementations):
    return lambda impl_name: variants_implementations[impl_name]


@pytest.fixture(scope="session")
def config_dae():
    def builder(path):
        fullpath = relative_to_this_test_folder(os.path.join("fixtures", path))
        config = from_prefix_dae(fullpath)
        return config

    return builder


def pytest_addoption(parser):
    parser.addoption(
        "--reimport", action="store_true",
        default=False, help="force reimport",
    )


@pytest.fixture(scope="session")
def reimport(request):
    return bool(request.config.getoption("--reimport"))


def collect_vcf(dirname):
    result = []
    pattern = os.path.join(dirname, "*.vcf")
    for filename in glob.glob(pattern):
        prefix = os.path.splitext(filename)[0]
        vcf_config = from_prefix_vcf(prefix)
        result.append(vcf_config)
    return result


def _import_project_from_prefix_config(
        config, root_path, gpf_instance, study_id=None):
    logger.debug("importing: %s", config)

    study_id = study_id or study_id_from_path(config.pedigree)
    study_temp_dirname = os.path.join(root_path, study_id)

    project = {
        "id": study_id,
        "processing_config": {
            "work_dir": study_temp_dirname,
            "include_reference": True,
        },
        "input": {
            "pedigree": {
                "file": config.pedigree,
            },
        },
        "destination": {
            "storage_id": "impala_test_storage",
        },
    }

    if config.denovo:
        project["input"]["denovo"] = {
            "files": [
                config.denovo,
            ],
        }
        if config.denovo.endswith("tsv"):
            project["input"]["denovo"].update({
                "genotype": "genotype",
                "family_id": "family",
                "chrom": "chrom",
                "pos": "pos",
                "ref": "ref",
                "alt": "alt",
            })
    if config.vcf:
        project["input"]["vcf"] = {
            "files": [
                config.vcf,
            ],
            "include_reference_genotypes": True,
            "include_unknown_family_genotypes": True,
            "include_unknown_person_genotypes": True,
            "multi_loader_fill_in_mode": "reference",
            "denovo_mode": "denovo",
            "omission_mode": "omission",
        }

    return ImportProject.build_from_config(project, gpf_instance=gpf_instance)


# @pytest.fixture(scope="session")
# def iossifov2014_import(
#         gpf_instance_2013,
#         fixture_dirname,
#         tmp_path_factory,
#         impala_host,
#         impala_genotype_storage,
#         reimport):

#     study_id = "iossifov_we2014_test"
#     from dae.impala_storage.helpers.impala_helpers import ImpalaHelpers

#     impala_helpers = ImpalaHelpers(
#         impala_hosts=[impala_host], impala_port=21050)

#     (variant_table, pedigree_table) = \
#         impala_genotype_storage.study_tables(
#             FrozenBox({"id": study_id}))

#     if not reimport and \
#             impala_helpers.check_table(
#                 impala_test_dbname(), variant_table) and \
#             impala_helpers.check_table(
#                 impala_test_dbname(), pedigree_table):
#         return

#     gpf_instance_2013.genotype_storages.register_genotype_storage(
#         impala_genotype_storage)
#     config = from_prefix_denovo(
#         fixture_dirname("dae_iossifov2014/iossifov2014"))

#     root_path = tmp_path_factory.mktemp(
#         f"{study_id}_{impala_genotype_storage.get_db()}")
#     import_project = _import_project_from_prefix_config(
#         config, root_path, gpf_instance_2013, study_id=study_id)
#     run_with_project(import_project)


@pytest.fixture(scope="session")
def dae_calc_gene_sets(request, fixtures_gpf_instance):
    genotype_data_names = ["f1_group", "f2_group", "f3_group"]
    for dgs in genotype_data_names:
        genotype_data = fixtures_gpf_instance.get_genotype_data(dgs)
        assert genotype_data is not None

        DenovoGeneSetHelpers.build_collection(genotype_data)

    def remove_gene_sets():
        for dgs in genotype_data_names:
            genotype_data = fixtures_gpf_instance.get_genotype_data(dgs)
            # fmt:off
            cache_file = \
                DenovoGeneSetHelpers.denovo_gene_set_cache_file(
                    genotype_data.config, "phenotype",
                )
            # fmt:on
            if os.path.exists(cache_file):
                os.remove(cache_file)

    request.addfinalizer(remove_gene_sets)


PED1 = """
# SIMPLE TRIO
familyId,    personId,    dadId,    momId,    sex,   status,    role
f1,          m1,          0,        0,        2,     1,         mom
f1,          d1,          0,        0,        1,     1,         dad
f1,          p1,          d1,       m1,       1,     2,         prb
"""


@pytest.fixture(scope="session")
def fam1():
    families_loader = FamiliesLoader(StringIO(PED1), ped_sep=",")
    families = families_loader.load()
    family = families["f1"]
    assert len(family.trios) == 1
    return family


@pytest.fixture()
def grr_fixture(fixture_dirname):
    test_grr_location = fixture_dirname("genomic_resources")
    repositories = {
        "id": "test_grr",
        "type": "directory",
        "directory": f"{test_grr_location}",
    }

    return build_genomic_resource_repository(repositories)


# @pytest.fixture(scope="session")
# def s3_moto_server_url():
#     """Start a moto (i.e. mocked) s3 server and return its URL."""
#     # pylint: disable=protected-access,import-outside-toplevel
#     if "AWS_SECRET_ACCESS_KEY" not in os.environ:
#         os.environ["AWS_SECRET_ACCESS_KEY"] = "foo"
#     if "AWS_ACCESS_KEY_ID" not in os.environ:
#         os.environ["AWS_ACCESS_KEY_ID"] = "foo"
#     # from moto.server import ThreadedMotoServer  # type: ignore
#     # server = ThreadedMotoServer(ip_address="", port=0)
#     # server.start()
#     # server_address = server._server.server_address

#     host = os.environ.get("LOCALSTACK_HOST", "localhost")
#     yield f"http://{host}:4566"

#     # server.stop()


# @pytest.fixture(scope="session")
# def s3_client(s3_moto_server_url):
#     """Return a boto client connected to the moto server."""
#     from botocore.session import Session  # type: ignore

#     session = Session()
#     client = session.create_client("s3", endpoint_url=s3_moto_server_url)
#     return client


# @pytest.fixture()
# def s3_filesystem(s3_moto_server_url):
#     from s3fs.core import S3FileSystem  # type: ignore

#     S3FileSystem.clear_instance_cache()
#     s3 = S3FileSystem(anon=False,
#                       client_kwargs={"endpoint_url": s3_moto_server_url})
#     s3.invalidate_cache()
#     yield s3


# @pytest.fixture()
# def s3_tmp_bucket_url(s3_client, s3_filesystem):
#     """Create a bucket called 'test-bucket' and return its URL."""
#     with tempfile.TemporaryDirectory("s3_test_bucket") as tmp_path:
#         bucket_url = f"s3:/{tmp_path}"
#         s3_filesystem.mkdir(bucket_url, acl="public-read")

#         yield bucket_url

#         s3_filesystem.rm(bucket_url, recursive=True)
