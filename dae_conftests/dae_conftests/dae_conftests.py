# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os
import sys
import glob
import shutil
import tempfile
import logging
from pathlib import Path

from io import StringIO

import pandas as pd
import pytest

from box import Box

from dae.gpf_instance.gpf_instance import GPFInstance, cached

from dae.configuration.gpf_config_parser import GPFConfigParser, FrozenBox
from dae.configuration.schemas.dae_conf import dae_conf_schema

from dae.annotation.annotation_factory import build_annotation_pipeline

from dae.backends.raw.loader import EffectAnnotationDecorator, \
    AnnotationPipelineDecorator
from dae.backends.raw.raw_variants import RawMemoryVariants

from dae.backends.dae.loader import DaeTransmittedLoader, DenovoLoader
from dae.backends.vcf.loader import VcfLoader

from dae.backends.impala.import_commons import \
    construct_import_effect_annotator


from dae.pedigrees.loader import FamiliesLoader
from dae.utils.helpers import study_id_from_path

from dae.backends.storage.impala_genotype_storage import ImpalaGenotypeStorage

from dae.gene.denovo_gene_set_collection_factory import \
    DenovoGeneSetCollectionFactory
from dae.autism_gene_profile.statistic import AGPStatistic
from dae.autism_gene_profile.db import AutismGeneProfileDB
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.group_repository import GenomicResourceGroupRepo
from dae.genomic_resources.gene_models import \
    load_gene_models_from_resource
from dae.genomic_resources.reference_genome import \
    open_reference_genome_from_resource


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


@pytest.fixture()
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

    class GPFInstanceInternal(GPFInstance):
        def __init__(self, *args, **kwargs):
            super(GPFInstanceInternal, self).__init__(*args, **kwargs)

    def build(work_dir=None, load_eagerly=False):
        instance = GPFInstanceInternal(
            work_dir=work_dir, load_eagerly=load_eagerly
        )
        repositories = [
            instance.grr
        ]

        repositories.append(
            build_genomic_resource_repository(
                Box({
                    "id": "fixtures",
                    "type": "directory",
                    "directory":
                        f"{fixture_dirname('genomic_resources')}"
                })))
        instance.grr = GenomicResourceGroupRepo(repositories)

        return instance

    return build


@pytest.fixture(scope="session")
def gpf_instance_2013(
        default_dae_config, fixture_dirname, global_dae_fixtures_dir):

    class GPFInstance2013(GPFInstance):
        def __init__(self, *args, **kwargs):
            super(GPFInstance2013, self).__init__(*args, **kwargs)

        @property  # type: ignore
        @cached
        def gene_models(self):
            print(self.dae_config.gene_models)
            resource = self.grr.get_resource(
                "hg19/gene_models/refGene_v201309")
            result = load_gene_models_from_resource(resource)
            return result

    gpf_instance = GPFInstance2013(dae_config=default_dae_config)

    repositories = [
        gpf_instance.grr
    ]
    repositories.append(
        build_genomic_resource_repository(
            {
                "id": "fixtures",
                "type": "directory",
                "directory": f"{fixture_dirname('genomic_resources')}"
            }))
    gpf_instance.grr = GenomicResourceGroupRepo(repositories)

    return gpf_instance


@pytest.fixture(scope="session")
def fixtures_gpf_instance(gpf_instance, global_dae_fixtures_dir):
    return gpf_instance(global_dae_fixtures_dir)


@pytest.fixture(scope="session")
def gpf_instance_2019(default_dae_config, global_dae_fixtures_dir):

    class GPFInstance2019(GPFInstance):
        def __init__(self, *args, **kwargs):
            super(GPFInstance2019, self).__init__(*args, **kwargs)

        @property  # type: ignore
        @cached
        def gene_models(self):
            resource = self.grr.get_resource(
                "hg19/gene_models/refGene_v20190211")
            result = load_gene_models_from_resource(resource)
            return result

    return GPFInstance2019(
        dae_config=default_dae_config, work_dir=global_dae_fixtures_dir
    )


def _create_gpf_instance(
        gene_model_dir, ref_genome_dir,
        default_dae_config, global_dae_fixtures_dir, fixture_dirname):
    class CustomGPFInstance(GPFInstance):
        def __init__(self, *args, **kwargs):
            super(CustomGPFInstance, self).__init__(*args, **kwargs)

        @property  # type: ignore
        @cached
        def gene_models(self):
            if gene_model_dir is None:
                return super().gene_models
            resource = self.grr.get_resource(gene_model_dir)
            result = load_gene_models_from_resource(resource)
            return result

        @property  # type: ignore
        @cached
        def reference_genome(self):
            if ref_genome_dir is None:
                return super().reference_genome
            resource = self.grr.get_resource(ref_genome_dir)
            result = open_reference_genome_from_resource(resource)
            return result

    instance = CustomGPFInstance(
        dae_config=default_dae_config, work_dir=global_dae_fixtures_dir
    )
    repositories = [
        instance.grr
    ]
    repositories.append(
        build_genomic_resource_repository(
            {
                "id": "fixtures",
                "type": "directory",
                "directory": f"{fixture_dirname('genomic_resources')}"
            }))
    instance.grr = GenomicResourceGroupRepo(repositories)

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
    denovo_filename = "{}.txt".format(prefix)
    family_filename = "{}_families.ped".format(prefix)

    conf = {
        "denovo": {
            "denovo_filename": denovo_filename,
            "family_filename": family_filename,
        }
    }
    return FrozenBox(conf)


def from_prefix_vcf(prefix):
    pedigree_filename = f"{prefix}.ped"
    assert os.path.exists(pedigree_filename)
    conf = {
        "prefix": prefix,
        "pedigree": pedigree_filename,
    }

    vcf_filename = "{}.vcf".format(prefix)
    if not os.path.exists(vcf_filename):
        vcf_filename = "{}.vcf.gz".format(prefix)
    if os.path.exists(vcf_filename):
        conf["vcf"] = vcf_filename

    denovo_filename = f"{prefix}.tsv"
    if os.path.exists(denovo_filename):
        conf["denovo"] = denovo_filename
    return FrozenBox(conf)


@pytest.fixture
def dae_denovo_config():
    fullpath = relative_to_this_test_folder("fixtures/dae_denovo/denovo")
    config = from_prefix_denovo(fullpath)
    return config.denovo


@pytest.fixture
def dae_denovo(
        dae_denovo_config, gpf_instance_2013, annotation_pipeline_internal):

    families_loader = FamiliesLoader(
        dae_denovo_config.family_filename, **{"ped_file_format": "simple"}
    )
    families = families_loader.load()

    variants_loader = DenovoLoader(
        families, dae_denovo_config.denovo_filename,
        gpf_instance_2013.reference_genome
    )

    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal
    )
    fvars = RawMemoryVariants([variants_loader], families=families)
    return fvars


def from_prefix_dae(prefix):
    summary_filename = "{}.txt.gz".format(prefix)
    toomany_filename = "{}-TOOMANY.txt.gz".format(prefix)
    family_filename = "{}.families.txt".format(prefix)

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
def dae_iossifov2014_config():
    fullpath = relative_to_this_test_folder(
        "fixtures/dae_iossifov2014/iossifov2014"
    )
    config = from_prefix_denovo(fullpath)
    return config.denovo


@pytest.fixture
def iossifov2014_loader(
        dae_iossifov2014_config,
        gpf_instance_2013, annotation_pipeline_internal):

    config = dae_iossifov2014_config

    families_loader = FamiliesLoader(config.family_filename)
    families = families_loader.load()

    variants_loader = DenovoLoader(
        families, config.denovo_filename,
        gpf_instance_2013.reference_genome
    )

    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal
    )

    return variants_loader, families_loader


@pytest.fixture
def iossifov2014_raw_denovo(iossifov2014_loader):

    variants_loader, families_loader = iossifov2014_loader
    fvars = RawMemoryVariants(
        [variants_loader], families_loader.load()
    )

    return fvars


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


@pytest.fixture(scope="session")
def raw_dae(config_dae, gpf_instance_2013):
    def builder(path, region=None):
        config = config_dae(path)

        ped_df = FamiliesLoader.load_simple_family_file(
            dae_transmitted_config.family_filename
        )

        dae = DaeTransmittedLoader(
            config.dae.summary_filename,
            config.dae.toomany_filename,
            ped_df,
            region=region,
            genome=gpf_instance_2013.reference_genome,
        )
        return dae

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
def impala_genotype_storage(hdfs_host, impala_host):
    storage_config = FrozenBox(
        {
            "id": "impala_test_storage",
            "type": "impala",
            "dir": "/tmp",
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
    )

    return ImpalaGenotypeStorage(storage_config, "impala_test_storage")


@pytest.fixture(scope="session")
def impala_helpers(impala_genotype_storage):
    return impala_genotype_storage.impala_helpers


def collect_vcf(dirname):
    result = []
    pattern = os.path.join(dirname, "*.vcf")
    for filename in glob.glob(pattern):
        prefix = os.path.splitext(filename)[0]
        vcf_config = from_prefix_vcf(prefix)
        result.append(vcf_config)
    return result


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

    from dae.backends.impala.hdfs_helpers import HdfsHelpers

    hdfs = HdfsHelpers(hdfs_host, 8020)

    temp_dirname = hdfs.tempdir(prefix="variants_", suffix="_data")
    hdfs.mkdir(temp_dirname)

    def fin():
        hdfs.delete(temp_dirname, recursive=True)

    request.addfinalizer(fin)

    effect_annotator = construct_import_effect_annotator(
        gpf_instance_2013
    )

    from dae.backends.impala.impala_helpers import ImpalaHelpers

    impala_helpers = ImpalaHelpers(
        impala_hosts=[impala_host], impala_port=21050)

    def build(dirname):

        if not impala_helpers.check_database(impala_test_dbname()):
            impala_helpers.create_database(impala_test_dbname())

        vcfdirname = relative_to_this_test_folder(
            os.path.join("fixtures", dirname)
        )
        vcf_configs = collect_vcf(vcfdirname)

        for config in vcf_configs:
            logger.debug(f"importing: {config}")

            filename = os.path.basename(config.pedigree)
            study_id = os.path.splitext(filename)[0]

            (variant_table, pedigree_table) = \
                impala_genotype_storage.study_tables(
                    FrozenBox({"id": study_id}))

            if (
                not reimport
                and impala_helpers.check_table(
                    impala_test_dbname(), variant_table
                )
                and impala_helpers.check_table(
                    impala_test_dbname(), pedigree_table
                )
            ):
                continue

            study_id = study_id_from_path(config.pedigree)
            study_temp_dirname = os.path.join(temp_dirname, study_id)

            families_loader = FamiliesLoader(config.pedigree)
            families = families_loader.load()
            genome = gpf_instance_2013.reference_genome

            loaders = []
            if config.denovo:
                denovo_loader = DenovoLoader(
                    families,
                    config.denovo,
                    genome,
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
                genome,
                regions=None,
                params={
                    "vcf_include_reference_genotypes": True,
                    "vcf_include_unknown_family_genotypes": True,
                    "vcf_include_unknown_person_genotypes": True,
                    "vcf_multi_loader_fill_in_mode": "reference",
                    "vcf_denovo_mode": "denovo",
                    "vcf_omission_mode": "omission",
                },
            )

            loaders.append(EffectAnnotationDecorator(
                vcf_loader, effect_annotator))

            impala_genotype_storage.simple_study_import(
                study_id,
                families_loader=families_loader,
                variant_loaders=loaders,
                output=study_temp_dirname,
                include_reference=True)

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


@pytest.fixture
def iossifov2014_impala(
        request,
        iossifov2014_loader,
        gpf_instance_2013,
        hdfs_host,
        impala_host,
        impala_genotype_storage,
        reimport):

    study_id = "iossifov_we2014_test"

    from dae.backends.impala.impala_helpers import ImpalaHelpers

    impala_helpers = ImpalaHelpers(
        impala_hosts=[impala_host], impala_port=21050)

    (variant_table, pedigree_table) = \
        impala_genotype_storage.study_tables(
            FrozenBox({"id": study_id}))

    if reimport or \
            not impala_helpers.check_table(
                "impala_test_db", variant_table) or \
            not impala_helpers.check_table(
                "impala_test_db", pedigree_table):

        from dae.backends.impala.hdfs_helpers import HdfsHelpers

        hdfs = HdfsHelpers(hdfs_host, 8020)

        temp_dirname = hdfs.tempdir(prefix="variants_", suffix="_data")
        hdfs.mkdir(temp_dirname)

        study_temp_dirname = os.path.join(temp_dirname, study_id)
        variants_loader, families_loader = iossifov2014_loader

        impala_genotype_storage.simple_study_import(
            study_id,
            families_loader=families_loader,
            variant_loaders=[variants_loader],
            output=study_temp_dirname)

    fvars = impala_genotype_storage.build_backend(
        FrozenBox({"id": study_id}), gpf_instance_2013.reference_genome,
        gpf_instance_2013.gene_models
    )
    return fvars


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
def agp_config(data_import, iossifov2014_impala):
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
    fixtures_gpf_instance.__autism_gene_profile_db = \
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


# Code copy/pasted from
# https://github.com/fsspec/s3fs/blob/main/s3fs/tests/test_s3fs.py#L67
port = 5555
endpoint_uri = "http://127.0.0.1:%s/" % port


@pytest.fixture()
def s3_base():
    import time
    import requests

    # writable local S3 system
    import shlex
    import subprocess

    try:
        # should fail since we didn't start server yet
        r = requests.get(endpoint_uri)
    except Exception:  # noqa
        pass
    else:
        if r.ok:
            raise RuntimeError("moto server already up")
    if "AWS_SECRET_ACCESS_KEY" not in os.environ:
        os.environ["AWS_SECRET_ACCESS_KEY"] = "foo"
    if "AWS_ACCESS_KEY_ID" not in os.environ:
        os.environ["AWS_ACCESS_KEY_ID"] = "foo"
    proc = subprocess.Popen(shlex.split("moto_server s3 -p %s" % port))

    timeout = 5
    while timeout > 0:
        try:
            r = requests.get(endpoint_uri)
            if r.ok:
                break
        except Exception:  # noqa
            pass
        timeout -= 0.1
        time.sleep(0.1)
    yield
    proc.terminate()
    proc.wait()


def get_boto3_client():
    from botocore.session import Session  # type: ignore

    # NB: we use the sync botocore client for setup
    session = Session()
    return session.create_client("s3", endpoint_url=endpoint_uri)


@pytest.fixture()
def s3(s3_base):
    from s3fs.core import S3FileSystem  # type: ignore

    client = get_boto3_client()
    client.create_bucket(Bucket="test-bucket", ACL="public-read")

    S3FileSystem.clear_instance_cache()
    s3 = S3FileSystem(anon=False, client_kwargs={"endpoint_url": endpoint_uri})
    s3.invalidate_cache()
    yield s3
