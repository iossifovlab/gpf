# pylint: disable=W0621,C0114,C0116,C0415,W0212,W0613,C0302,C0115,W0102,W0603

import os
import sys
import glob
import shutil
import tempfile
import logging
from pathlib import Path
from functools import cached_property

from io import StringIO

import pandas as pd
import pytest

from box import Box

from dae.configuration.gpf_config_parser import GPFConfigParser, FrozenBox, \
    DefaultBox

from dae.configuration.schemas.dae_conf import dae_conf_schema

from dae.annotation.annotation_factory import build_annotation_pipeline

from dae.variants_loaders.raw.loader import EffectAnnotationDecorator, \
    AnnotationPipelineDecorator
from dae.inmemory_storage.raw_variants import RawMemoryVariants

from dae.variants_loaders.dae.loader import DaeTransmittedLoader, DenovoLoader
from dae.variants_loaders.vcf.loader import VcfLoader
from dae.import_tools.import_tools import ImportProject, run_with_project

from dae.impala_storage.schema1.import_commons import \
    construct_import_effect_annotator


from dae.pedigrees.loader import FamiliesLoader
from dae.utils.helpers import study_id_from_path

from dae.gene.denovo_gene_set_collection_factory import \
    DenovoGeneSetCollectionFactory
from dae.autism_gene_profile.statistic import AGPStatistic
from dae.autism_gene_profile.db import AutismGeneProfileDB
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.group_repository import GenomicResourceGroupRepo
from dae.genomic_resources.gene_models import \
    build_gene_models_from_resource
from dae.genomic_resources.reference_genome import \
    build_reference_genome_from_resource


logger = logging.getLogger(__name__)


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "tests", path
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
        conf_dir=conf_dir
    )
    return dae_config


@pytest.fixture(scope="session")
def gpf_instance(default_dae_config, fixture_dirname):
    from dae.gpf_instance.gpf_instance import GPFInstance

    def build(config_filename):
        repositories = [
            build_genomic_resource_repository(
                {
                    "id": "grr_test_repo",
                    "type": "directory",
                    "directory": fixture_dirname("test_repo"),
                }
            ),
            build_genomic_resource_repository(
                {
                    "id": "fixtures",
                    "type": "directory",
                    "directory": fixture_dirname("genomic_resources")
                }),
            build_genomic_resource_repository(),
        ]
        grr = GenomicResourceGroupRepo(repositories)

        instance = GPFInstance.build(config_filename, grr=grr)

        return instance

    return build


@pytest.fixture(scope="session")
def gpf_instance_2013(
        default_dae_config, fixture_dirname, global_dae_fixtures_dir):
    from dae.gpf_instance.gpf_instance import GPFInstance

    class GPFInstance2013(GPFInstance):

        @cached_property
        def gene_models(self):
            print(self.dae_config.gene_models)
            resource = self.grr.get_resource(
                "hg19/gene_models/refGene_v201309")
            result = build_gene_models_from_resource(resource)
            result.load()
            return result

    repositories = [
        build_genomic_resource_repository({
            "id": "grr_test_repo",
            "type": "directory",
            "directory": fixture_dirname("test_repo"),
        }),
        build_genomic_resource_repository({
            "id": "fixtures",
            "type": "directory",
            "directory": fixture_dirname("genomic_resources")
        }),
        build_genomic_resource_repository(),
    ]
    grr = GenomicResourceGroupRepo(repositories)
    gpf_instance = GPFInstance2013(
        dae_config=default_dae_config,
        dae_dir=global_dae_fixtures_dir,
        grr=grr)

    return gpf_instance


@pytest.fixture(scope="session")
def fixtures_gpf_instance(gpf_instance, global_dae_fixtures_dir):
    return gpf_instance(
        os.path.join(global_dae_fixtures_dir, "gpf_instance.yaml"))


@pytest.fixture(scope="session")
def gpf_instance_2019(
        default_dae_config, fixture_dirname, global_dae_fixtures_dir):
    from dae.gpf_instance.gpf_instance import GPFInstance

    class GPFInstance2019(GPFInstance):

        @cached_property
        def gene_models(self):
            resource = self.grr.get_resource(
                "hg19/gene_models/refGene_v20190211")
            result = build_gene_models_from_resource(resource)
            result.load()
            return result

    repositories = [
        build_genomic_resource_repository({
            "id": "grr_test_repo",
            "type": "directory",
            "directory": fixture_dirname("test_repo"),
        }),
        build_genomic_resource_repository({
            "id": "fixtures",
            "type": "directory",
            "directory": fixture_dirname("genomic_resources")
        }),
        build_genomic_resource_repository(),
    ]
    grr = GenomicResourceGroupRepo(repositories)
    gpf_instance = GPFInstance2019(
        dae_config=default_dae_config, dae_dir=global_dae_fixtures_dir,
        grr=grr)

    return gpf_instance


def _create_gpf_instance(
        gene_model_dir, ref_genome_dir,
        default_dae_config, global_dae_fixtures_dir, fixture_dirname):
    from dae.gpf_instance.gpf_instance import GPFInstance

    class CustomGPFInstance(GPFInstance):

        @cached_property
        def gene_models(self):
            if gene_model_dir is None:
                return super().gene_models
            resource = self.grr.get_resource(gene_model_dir)
            result = build_gene_models_from_resource(resource)
            result.load()
            return result

        @cached_property
        def reference_genome(self):
            if ref_genome_dir is None:
                return super().reference_genome
            resource = self.grr.get_resource(ref_genome_dir)
            result = build_reference_genome_from_resource(resource)
            result.open()
            return result
    repositories = [
        build_genomic_resource_repository({
            "id": "grr_test_repo",
            "type": "directory",
            "directory": fixture_dirname("test_repo"),
        }),
        build_genomic_resource_repository({
            "id": "fixtures",
            "type": "directory",
            "directory": fixture_dirname("genomic_resources")
        }),
        build_genomic_resource_repository(),
    ]
    grr = GenomicResourceGroupRepo(repositories)

    instance = CustomGPFInstance(
        dae_config=default_dae_config, dae_dir=global_dae_fixtures_dir,
        grr=grr
    )

    return instance


@pytest.fixture(scope="session")
def gpf_instance_short(
        default_dae_config, global_dae_fixtures_dir, fixture_dirname):
    return _create_gpf_instance(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/\
gene_models/refGene_201309",
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome",
        default_dae_config, global_dae_fixtures_dir, fixture_dirname
    )


@pytest.fixture(scope="session")
def gpf_instance_grch38(
        default_dae_config, global_dae_fixtures_dir, fixture_dirname):
    return _create_gpf_instance(
        "hg38/GRCh38-hg38/gene_models/refSeq_20200330",
        "hg38/GRCh38-hg38/genome",
        default_dae_config, global_dae_fixtures_dir, fixture_dirname
    )


@pytest.fixture
def result_df():
    def build(data):
        infile = StringIO(str(data))
        df = pd.read_csv(infile, sep="\t")
        return df

    return build


@pytest.fixture
def temp_dirname(request):
    dirname = tempfile.mkdtemp(suffix="_data", prefix="variants_")

    def fin():
        shutil.rmtree(dirname)

    request.addfinalizer(fin)
    return dirname


@pytest.fixture
def temp_dirname_grdb(request):
    dirname = tempfile.mkdtemp(suffix="_data", prefix="grdb_")

    def fin():
        shutil.rmtree(dirname)

    request.addfinalizer(fin)
    return dirname


@pytest.fixture
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
    filename = relative_to_this_test_folder(IMPORT_ANNOTATION_CONFIG)
    return filename


@pytest.fixture(scope="session")
def annotation_pipeline_default_config(default_dae_config):
    return default_dae_config.annotation.conf_file


@pytest.fixture(scope="session")
def annotation_scores_dirname():
    filename = relative_to_this_test_folder("fixtures/annotation_pipeline/")
    return filename


@pytest.fixture
def annotation_pipeline_vcf(gpf_instance_2013):
    filename = relative_to_this_test_folder(IMPORT_ANNOTATION_CONFIG)
    pipeline = build_annotation_pipeline(
        pipeline_config_file=filename, grr_repository=gpf_instance_2013.grr)
    return pipeline


@pytest.fixture
def annotation_pipeline_internal(gpf_instance_2013):
    filename = relative_to_this_test_folder(IMPORT_ANNOTATION_CONFIG)
    pipeline = build_annotation_pipeline(
        pipeline_config_file=filename, grr_repository=gpf_instance_2013.grr)
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


@pytest.fixture
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
        }
    }
    return FrozenBox(conf)


@pytest.fixture
def dae_transmitted_config():
    fullpath = relative_to_this_test_folder(
        "fixtures/dae_transmitted/transmission"
    )
    config = from_prefix_dae(fullpath)
    return config.dae


@pytest.fixture
def dae_transmitted(
    dae_transmitted_config, gpf_instance_2013, annotation_pipeline_internal
):

    families = FamiliesLoader.load_simple_families_file(
        dae_transmitted_config.family_filename
    )

    variants_loader = DaeTransmittedLoader(
        families,
        dae_transmitted_config.summary_filename,
        genome=gpf_instance_2013.reference_genome,
        regions=None,
    )
    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal
    )

    return variants_loader


@pytest.fixture
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
        gpf_instance_2013.reference_genome
    )

    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal
    )

    return variants_loader, families_loader


@pytest.fixture(scope="session")
def vcf_loader_data():
    def builder(path):
        if os.path.isabs(path):
            prefix = path
        else:
            prefix = os.path.join(
                relative_to_this_test_folder("fixtures"), path
            )
        conf = from_prefix_vcf(prefix)
        return conf

    return builder


@pytest.fixture(scope="session")
def vcf_variants_loaders(
        vcf_loader_data, gpf_instance_2019):

    effect_annotator = construct_import_effect_annotator(
        gpf_instance_2019
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
                }
            )
            loaders.append(EffectAnnotationDecorator(
                denovo_loader, effect_annotator))

        vcf_loader = VcfLoader(
            families,
            [config.vcf],
            gpf_instance_2019.reference_genome,
            params=params
        )

        loaders.append(EffectAnnotationDecorator(
            vcf_loader, effect_annotator
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


@pytest.fixture
def variants_implementations(variants_impala, variants_vcf):
    impls = {"variants_impala": variants_impala, "variants_vcf": variants_vcf}
    return impls


@pytest.fixture
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
        default=False, help="force reimport"
    )
    parser.addoption(
        "--logger-default", default="ERROR",
        help="default logging level"
    )
    parser.addoption(
        "--logger-debug",
        default=[],
        type=str,
        nargs="+",
        help="list of loggers with logging level DEBUG"
    )
    parser.addoption(
        "--logger-info",
        default=[],
        type=str,
        nargs="+",
        help="list of loggers with logging level INFO"
    )
    parser.addoption(
        "--logger-warning",
        default=[],
        type=str,
        nargs="+",
        help="list of loggers with logging level WARNING"
    )

    parser.addoption(
        "--logger-error",
        default=[],
        type=str,
        nargs="+",
        help="list of loggers with logging level ERROR"
    )


def pytest_configure(config):

    logging_level_opt = config.getoption("--logger-default")
    print("default logging level:", logging_level_opt)

    if logging_level_opt == "DEBUG":
        level = logging.DEBUG
    elif logging_level_opt == "INFO":
        level = logging.INFO
    elif logging_level_opt == "WARNING":
        level = logging.WARNING
    elif logging_level_opt == "ERROR":
        level = logging.ERROR
    else:
        raise ValueError(f"wrong loggge default level: {logging_level_opt}")

    logging.basicConfig(
        stream=sys.stderr, level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # suppress impala logger
    logging.getLogger("impala") \
        .setLevel(logging.WARNING)

    # suppress url connection pool
    logging.getLogger("urllib3.connectionpool") \
        .setLevel(logging.INFO)

    # suppress fsspec
    logging.getLogger("fsspec") \
        .setLevel(logging.INFO)

    loggers = config.getoption("--logger-error")
    for logger_name in loggers:
        logging.getLogger(logger_name).setLevel(logging.ERROR)

    loggers = config.getoption("--logger-warning")
    for logger_name in loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    loggers = config.getoption("--logger-info")
    for logger_name in loggers:
        logging.getLogger(logger_name).setLevel(logging.INFO)

    loggers = config.getoption("--logger-debug")
    for logger_name in loggers:
        logging.getLogger(logger_name).setLevel(logging.DEBUG)


@pytest.fixture(scope="session")
def reimport(request):
    return bool(request.config.getoption("--reimport"))


@pytest.fixture(scope="session")
def hdfs_host():
    return os.environ.get("DAE_HDFS_HOST", "127.0.0.1")


@pytest.fixture(scope="session")
def impala_host():
    return os.environ.get("DAE_IMPALA_HOST", "127.0.0.1")


def impala_test_dbname():
    return "impala_test_db"


@pytest.fixture(scope="session")
def impala_genotype_storage(request, hdfs_host, impala_host):

    storage_config = {
        "id": "impala_test_storage",
        "storage_type": "impala",
        "impala": {
            "hosts": [impala_host],
            "port": 21050,
            "db": impala_test_dbname(),
            "pool_size": 5,
        },
        "hdfs": {
            "host": hdfs_host,
            "port": 8020,
            "base_dir": "/tmp/test_data"},
    }
    from dae.genotype_storage.genotype_storage_registry import \
        GenotypeStorageRegistry
    registry = GenotypeStorageRegistry()
    registry.register_storage_config(storage_config)

    def fin():
        registry.shutdown()
    request.addfinalizer(fin)

    return registry.get_genotype_storage("impala_test_storage")


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
            }
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


DATA_IMPORT_COUNT = 0


@pytest.fixture(scope="session")
def data_import(
        request,
        hdfs_host,
        impala_host,
        impala_genotype_storage,
        reimport,
        default_dae_config,
        gpf_instance_2013):

    global DATA_IMPORT_COUNT
    DATA_IMPORT_COUNT += 1

    assert DATA_IMPORT_COUNT == 1

    from dae.impala_storage.helpers.hdfs_helpers import HdfsHelpers

    hdfs = HdfsHelpers(hdfs_host, 8020)

    temp_dirname = hdfs.tempdir(prefix="variants_", suffix="_data")
    hdfs.mkdir(temp_dirname)

    def fin():
        hdfs.delete(temp_dirname, recursive=True)

    request.addfinalizer(fin)

    from dae.impala_storage.helpers.impala_helpers import ImpalaHelpers

    impala_helpers = ImpalaHelpers(
        impala_hosts=[impala_host], impala_port=21050)
    gpf_instance_2013.genotype_storages.register_genotype_storage(
        impala_genotype_storage)

    def build(dirname):

        if not impala_helpers.check_database(impala_test_dbname()):
            impala_helpers.create_database(impala_test_dbname())

        vcfdirname = relative_to_this_test_folder(
            os.path.join("fixtures", dirname)
        )
        vcf_configs = collect_vcf(vcfdirname)

        for config in vcf_configs:
            logger.debug("importing: %s", config)

            study_id = study_id_from_path(config.pedigree)
            (variant_table, pedigree_table) = \
                impala_genotype_storage.study_tables(
                    FrozenBox({"id": study_id}))

            if not reimport and \
                    impala_helpers.check_table(
                        impala_test_dbname(), variant_table) and \
                    impala_helpers.check_table(
                        impala_test_dbname(), pedigree_table):
                continue

            import_project = _import_project_from_prefix_config(
                config, temp_dirname, gpf_instance_2013)

            run_with_project(import_project)

    build("backends/")
    return True


@pytest.fixture(scope="session")
def variants_impala(
        request, data_import, impala_genotype_storage, gpf_instance_2013):

    def builder(path):
        study_id = os.path.basename(path)
        fvars = impala_genotype_storage.build_backend(
            FrozenBox({"id": study_id}),
            gpf_instance_2013.reference_genome,
            gpf_instance_2013.gene_models
        )
        return fvars

    return builder


@pytest.fixture(scope="session")
def iossifov2014_import(
        gpf_instance_2013,
        fixture_dirname,
        tmp_path_factory,
        impala_host,
        impala_genotype_storage,
        reimport):

    study_id = "iossifov_we2014_test"
    from dae.impala_storage.helpers.impala_helpers import ImpalaHelpers

    impala_helpers = ImpalaHelpers(
        impala_hosts=[impala_host], impala_port=21050)

    (variant_table, pedigree_table) = \
        impala_genotype_storage.study_tables(
            FrozenBox({"id": study_id}))

    if not reimport and \
            impala_helpers.check_table(
                impala_test_dbname(), variant_table) and \
            impala_helpers.check_table(
                impala_test_dbname(), pedigree_table):
        return

    gpf_instance_2013.genotype_storages.register_genotype_storage(
        impala_genotype_storage)
    config = from_prefix_denovo(
        fixture_dirname("dae_iossifov2014/iossifov2014"))

    root_path = tmp_path_factory.mktemp(
        f"{study_id}_{impala_genotype_storage.get_db()}")
    import_project = _import_project_from_prefix_config(
        config, root_path, gpf_instance_2013, study_id=study_id)
    run_with_project(import_project)


@pytest.fixture(scope="session")
def dae_calc_gene_sets(request, fixtures_gpf_instance):
    genotype_data_names = ["f1_group", "f2_group", "f3_group"]
    for dgs in genotype_data_names:
        genotype_data = fixtures_gpf_instance.get_genotype_data(dgs)
        assert genotype_data is not None

        DenovoGeneSetCollectionFactory.build_collection(genotype_data)

    def remove_gene_sets():
        for dgs in genotype_data_names:
            genotype_data = fixtures_gpf_instance.get_genotype_data(dgs)
            # fmt:off
            cache_file = \
                DenovoGeneSetCollectionFactory.denovo_gene_set_cache_file(
                    genotype_data.config, "phenotype"
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


@pytest.fixture
def temp_dbfile(request):
    dbfile = tempfile.mktemp(prefix="dbfile_")  # NOSONAR

    def fin():
        if os.path.exists(dbfile):
            os.remove(dbfile)

    request.addfinalizer(fin)
    return dbfile


@pytest.fixture
def agp_config(iossifov2014_import):
    return Box({
        "gene_sets": [
            {
                "category": "relevant_gene_sets",
                "display_name": "Relevant Gene Sets",
                "sets": [
                    {"set_id": "CHD8 target genes", "collection_id": "main"},
                    {
                        "set_id": "FMRP Darnell",
                        "collection_id": "main"
                    }
                ]
            },
        ],
        "genomic_scores": [
            {
                "category": "protection_scores",
                "display_name": "Protection scores",
                "scores": [
                    {"score_name": "SFARI_gene_score", "format": "%s"},
                    {"score_name": "RVIS_rank", "format": "%s"},
                    {"score_name": "RVIS", "format": "%s"}
                ]
            },
            {
                "category": "autism_scores",
                "display_name": "Autism scores",
                "scores": [
                    {"score_name": "SFARI_gene_score", "format": "%s"},
                    {"score_name": "RVIS_rank", "format": "%s"},
                    {"score_name": "RVIS", "format": "%s"}
                ]
            },
        ],
        "datasets": Box({
            "iossifov_we2014_test": Box({
                "statistics": [
                    {
                        "id": "denovo_noncoding",
                        "display_name": "Noncoding",
                        "effects": ["noncoding"],
                        "category": "denovo"
                    },
                    {
                        "id": "denovo_missense",
                        "display_name": "Missense",
                        "effects": ["missense"],
                        "category": "denovo"
                    }
                ],
                "person_sets": [
                    {
                        "set_name": "unknown",
                        "collection_name": "phenotype"
                    },
                    {
                        "set_name": "unaffected",
                        "collection_name": "phenotype"
                    },
                ]
            })
        })
    })


@pytest.fixture
def agp_gpf_instance(
        fixtures_gpf_instance, mocker, sample_agp, temp_dbfile, agp_config):
    from dae.gpf_instance.gpf_instance import GPFInstance

    mocker.patch.object(
        GPFInstance,
        "_autism_gene_profile_config",
        return_value=agp_config,
        new_callable=mocker.PropertyMock
    )
    main_gene_sets = {
        "CHD8 target genes",
        "FMRP Darnell",
        "FMRP Tuschl",
        "PSD",
        "autism candidates from Iossifov PNAS 2015",
        "autism candidates from Sanders Neuron 2015",
        "brain critical genes",
        "brain embryonically expressed",
        "chromatin modifiers",
        "essential genes",
        "non-essential genes",
        "postsynaptic inhibition",
        "synaptic clefts excitatory",
        "synaptic clefts inhibitory",
        "topotecan downreg genes"
    }
    mocker.patch.object(
        fixtures_gpf_instance.gene_sets_db,
        "get_gene_set_ids",
        return_value=main_gene_sets
    )
    fixtures_gpf_instance._autism_gene_profile_db = \
        AutismGeneProfileDB(
            fixtures_gpf_instance._autism_gene_profile_config,
            temp_dbfile,
            clear=True
        )
    print(temp_dbfile)
    fixtures_gpf_instance._autism_gene_profile_db.insert_agp(sample_agp)
    return fixtures_gpf_instance


@pytest.fixture(scope="session")
def sample_agp():
    gene_sets = ["main_CHD8 target genes"]
    genomic_scores = {
        "protection_scores": {
            "SFARI_gene_score": 1, "RVIS_rank": 193.0, "RVIS": -2.34
        },
        "autism_scores": {
            "SFARI_gene_score": 1, "RVIS_rank": 193.0, "RVIS": -2.34
        },
    }
    variant_counts = {
        "iossifov_we2014_test": {
            "unknown": {
                "denovo_noncoding": {"count": 53, "rate": 1},
                "denovo_missense": {"count": 21, "rate": 2}
            },
            "unaffected": {
                "denovo_noncoding": {"count": 43, "rate": 3},
                "denovo_missense": {"count": 51, "rate": 4}
            },
        }
    }
    return AGPStatistic(
        "CHD8", gene_sets, genomic_scores, variant_counts
    )


@pytest.fixture
def grr_fixture(fixture_dirname):
    test_grr_location = fixture_dirname("genomic_resources")
    repositories = {
        "id": "test_grr",
        "type": "directory",
        "directory": f"{test_grr_location}"
    }

    return build_genomic_resource_repository(repositories)


@pytest.fixture(scope="session")
def s3_moto_server_url():
    """Start a moto (i.e. mocked) s3 server and return its URL."""
    # pylint: disable=protected-access,import-outside-toplevel
    if "AWS_SECRET_ACCESS_KEY" not in os.environ:
        os.environ["AWS_SECRET_ACCESS_KEY"] = "foo"
    if "AWS_ACCESS_KEY_ID" not in os.environ:
        os.environ["AWS_ACCESS_KEY_ID"] = "foo"
    from moto.server import ThreadedMotoServer  # type: ignore
    server = ThreadedMotoServer(ip_address="", port=0)
    server.start()
    server_address = server._server.server_address

    yield f"http://{server_address[0]}:{server_address[1]}"

    server.stop()


@pytest.fixture(scope="session")
def s3_client(s3_moto_server_url):
    """Return a boto client connected to the moto server."""
    from botocore.session import Session  # type: ignore

    session = Session()
    client = session.create_client("s3", endpoint_url=s3_moto_server_url)
    return client


@pytest.fixture()
def s3_filesystem(s3_moto_server_url):
    from s3fs.core import S3FileSystem  # type: ignore

    S3FileSystem.clear_instance_cache()
    s3 = S3FileSystem(anon=False,
                      client_kwargs={"endpoint_url": s3_moto_server_url})
    s3.invalidate_cache()
    yield s3


@pytest.fixture()
def s3_tmp_bucket_url(s3_client, s3_filesystem):
    """Create a bucket called 'test-bucket' and return its URL."""
    bucket_url = "s3://test-bucket"
    s3_filesystem.mkdir(bucket_url, acl="public-read")

    yield bucket_url

    s3_filesystem.rm("s3://test-bucket", recursive=True)


@pytest.fixture(scope="session")
def fixtures_http_server():
    from dae.genomic_resources.testing import range_http_serve
    directory = relative_to_this_test_folder("fixtures/genomic_resources")
    with range_http_serve(directory) as httpd:
        yield httpd
