import pytest

import os
import glob
import shutil
import tempfile

import pandas as pd
from io import StringIO

from dae.genome.genomes_db import GenomesDB

from dae.gpf_instance.gpf_instance import GPFInstance, cached

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.dae_conf import dae_conf_schema

from dae.annotation.annotation_pipeline import PipelineAnnotator

from dae.variants.variant import SummaryVariant, SummaryAllele
from dae.variants.family_variant import FamilyVariant

from dae.backends.raw.loader import AnnotationPipelineDecorator
from dae.backends.raw.raw_variants import RawMemoryVariants

from dae.backends.dae.loader import DaeTransmittedLoader, DenovoLoader
from dae.backends.vcf.loader import VcfLoader

from dae.backends.impala.import_commons import (
    construct_import_annotation_pipeline,
)

from dae.pedigrees.family import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.utils.helpers import study_id_from_path

from dae.backends.impala.parquet_io import ParquetManager
from dae.backends.storage.impala_genotype_storage import ImpalaGenotypeStorage
from dae.gene.denovo_gene_set_collection_factory import (
    DenovoGeneSetCollectionFactory,
)


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


@pytest.fixture(scope="session")
def default_dae_config(request):
    studies_dirname = tempfile.mkdtemp(prefix="studies_", suffix="_test")

    def fin():
        shutil.rmtree(studies_dirname)

    request.addfinalizer(fin)
    dae_conf_path = os.path.join(
        os.environ.get("DAE_DB_DIR", None), "DAE.conf"
    )
    dae_config = GPFConfigParser.load_config(dae_conf_path, dae_conf_schema)
    dae_config = GPFConfigParser.modify_tuple(
        dae_config, {"studies_db": {"dir": studies_dirname}}
    )
    return dae_config


@pytest.fixture(scope="session")
def gpf_instance(default_dae_config):
    class GenomesDbInternal(GenomesDB):
        def get_default_gene_models_id(self, genome_id=None):
            return "RefSeq2013"

    class GPFInstanceInternal(GPFInstance):
        @property
        @cached
        def genomes_db(self):
            return GenomesDbInternal(
                default_dae_config.dae_data_dir,
                default_dae_config.genomes_db.conf_file,
            )

    def build(work_dir=None, load_eagerly=False):
        return GPFInstanceInternal(
            work_dir=work_dir, load_eagerly=load_eagerly
        )

    return build


@pytest.fixture(scope="session")
def gpf_instance_2013(default_dae_config, global_dae_fixtures_dir):
    class GenomesDb2013(GenomesDB):
        def get_gene_model_id(self, genome_id=None):
            return "RefSeq2013"

    class GPFInstance2013(GPFInstance):
        @property
        @cached
        def genomes_db(self):
            return GenomesDb2013(
                self.dae_config.dae_data_dir,
                self.dae_config.genomes_db.conf_file,
            )

    gpf_instance = GPFInstance2013(dae_config=default_dae_config)
    return gpf_instance


@pytest.fixture(scope="session")
def fixtures_gpf_instance(gpf_instance, global_dae_fixtures_dir):
    return gpf_instance(global_dae_fixtures_dir)


@pytest.fixture(scope="session")
def gene_models_2013(gpf_instance_2013):
    return gpf_instance_2013.genomes_db.get_gene_models("RefSeq2013")


@pytest.fixture(scope="session")
def genomes_db_2013(gpf_instance_2013):
    return gpf_instance_2013.genomes_db


@pytest.fixture(scope="session")
def genome_2013(gpf_instance_2013):
    return gpf_instance_2013.genomes_db.get_genome()


@pytest.fixture(scope="session")
def genomic_sequence_2013(genome_2013):
    return genome_2013.get_genomic_sequence()


@pytest.fixture(scope="session")
def gpf_instance_2019(default_dae_config, global_dae_fixtures_dir):
    class GenomesDb2019(GenomesDB):
        def get_gene_model_id(self, genome_id=None):
            return "RefSeq"

    class GPFInstance2019(GPFInstance):
        @property
        @cached
        def genomes_db(self):
            return GenomesDb2019(
                self.dae_config.dae_data_dir,
                self.dae_config.genomes_db.conf_file,
            )

    return GPFInstance2019(
        dae_config=default_dae_config, work_dir=global_dae_fixtures_dir
    )


@pytest.fixture(scope="session")
def gene_models_2019(gpf_instance_2019):
    return gpf_instance_2019.genomes_db.get_gene_models("RefSeq")


@pytest.fixture(scope="session")
def genomes_db_2019(gpf_instance_2019):
    return gpf_instance_2019.genomes_db


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
def temp_filename(request):
    dirname = tempfile.mkdtemp(suffix="_eff", prefix="variants_")

    def fin():
        shutil.rmtree(dirname)

    # request.addfinalizer(fin)
    output = os.path.join(dirname, "temp_filename.tmp")
    return output


@pytest.fixture(scope="session")
def annotation_pipeline_config():
    filename = relative_to_this_test_folder(
        "fixtures/annotation_pipeline/import_annotation.conf"
    )
    return filename


@pytest.fixture(scope="session")
def annotation_pipeline_default_config(default_dae_config):
    return default_dae_config.annotation.conf_file


@pytest.fixture(scope="session")
def default_annotation_pipeline(default_dae_config, genomes_db_2013):
    filename = default_dae_config.annotation.conf_file

    options = {
        "default_arguments": None,
        "vcf": True,
        "r": "reference",
        "a": "alternative",
        "c": "chrom",
        "p": "position",
    }

    pipeline = PipelineAnnotator.build(options, filename, genomes_db_2013)

    return pipeline


@pytest.fixture(scope="session")
def annotation_scores_dirname():
    filename = relative_to_this_test_folder("fixtures/annotation_pipeline/")
    return filename


@pytest.fixture(scope="session")
def annotation_pipeline_vcf(genomes_db_2013):
    filename = relative_to_this_test_folder(
        "fixtures/annotation_pipeline/import_annotation.conf"
    )

    options = {
        "default_arguments": None,
        "vcf": True,
        "scores_dirname": relative_to_this_test_folder(
            "fixtures/annotation_pipeline/"
        )
        # 'mode': 'overwrite',
    }

    pipeline = PipelineAnnotator.build(options, filename, genomes_db_2013,)
    return pipeline


@pytest.fixture(scope="session")
def annotation_pipeline_internal(genomes_db_2013):
    assert genomes_db_2013 is not None
    assert genomes_db_2013.get_gene_model_id() == "RefSeq2013"
    filename = relative_to_this_test_folder(
        "fixtures/annotation_pipeline/import_annotation.conf"
    )

    options = {
        "default_arguments": None,
        "vcf": True,
        "c": "chrom",
        "p": "position",
        "r": "reference",
        "a": "alternative",
        "scores_dirname": relative_to_this_test_folder(
            "fixtures/annotation_pipeline/"
        ),
    }

    pipeline = PipelineAnnotator.build(options, filename, genomes_db_2013,)
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
    return GPFConfigParser._dict_to_namedtuple(conf)


def from_prefix_vcf(prefix):
    vcf_filename = "{}.vcf".format(prefix)
    if not os.path.exists(vcf_filename):
        vcf_filename = "{}.vcf.gz".format(prefix)

    conf = {
        "pedigree": "{}.ped".format(prefix),
        "vcf": vcf_filename,
        "annotation": "{}-vcf-eff.txt".format(prefix),
        "prefix": prefix,
    }
    return GPFConfigParser._dict_to_namedtuple(conf)


@pytest.fixture
def dae_denovo_config():
    fullpath = relative_to_this_test_folder("fixtures/dae_denovo/denovo")
    config = from_prefix_denovo(fullpath)
    return config.denovo


@pytest.fixture
def dae_denovo(dae_denovo_config, genome_2013, annotation_pipeline_internal):

    families_loader = FamiliesLoader(
        dae_denovo_config.family_filename, params={"ped_file_format": "simple"}
    )
    families = families_loader.load()

    variants_loader = DenovoLoader(
        families, dae_denovo_config.denovo_filename, genome_2013
    )

    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal
    )
    fvars = RawMemoryVariants([variants_loader])
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
    return GPFConfigParser._dict_to_namedtuple(conf)


@pytest.fixture
def dae_transmitted_config():
    fullpath = relative_to_this_test_folder(
        "fixtures/dae_transmitted/transmission"
    )
    config = from_prefix_dae(fullpath)
    return config.dae


@pytest.fixture
def dae_transmitted(
    dae_transmitted_config, genome_2013, annotation_pipeline_internal
):

    # ped_df = FamiliesLoader.load_simple_family_file(
    #     dae_transmitted_config.family_filename
    # )
    families = FamiliesLoader.load_simple_families_file(
        dae_transmitted_config.family_filename
    )

    variants_loader = DaeTransmittedLoader(
        families,
        dae_transmitted_config.summary_filename,
        # dae_transmitted_config.toomany_filename,
        genome=genome_2013,
        regions=None,
    )
    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal
    )

    return variants_loader


@pytest.fixture(scope="session")
def dae_iossifov2014_config():
    fullpath = relative_to_this_test_folder(
        "fixtures/dae_iossifov2014/iossifov2014"
    )
    config = from_prefix_denovo(fullpath)
    return config.denovo


@pytest.fixture(scope="session")
def iossifov2014_loader(
    dae_iossifov2014_config, genome_2013, annotation_pipeline_internal
):
    config = dae_iossifov2014_config

    families_loader = FamiliesLoader(config.family_filename)
    families = families_loader.load()

    variants_loader = DenovoLoader(
        families, config.denovo_filename, genome_2013
    )

    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal
    )

    return variants_loader


@pytest.fixture(scope="session")
def iossifov2014_raw_denovo(iossifov2014_loader):

    fvars = RawMemoryVariants(
        [iossifov2014_loader], iossifov2014_loader.families
    )

    return fvars


@pytest.fixture(scope="session")
def iossifov2014_impala(
        request,
        iossifov2014_loader,
        genomes_db_2013,
        hdfs_host,
        impala_genotype_storage):

    from dae.backends.impala.hdfs_helpers import HdfsHelpers

    hdfs = HdfsHelpers(hdfs_host, 8020)

    temp_dirname = hdfs.tempdir(prefix="variants_", suffix="_data")
    hdfs.mkdir(temp_dirname)

    study_id = "iossifov_we2014_test"
    parquet_filenames = ParquetManager.build_parquet_filenames(
        temp_dirname, bucket_index=0, study_id=study_id
    )

    assert parquet_filenames is not None
    print(parquet_filenames)

    ParquetManager.families_to_parquet(
        iossifov2014_loader.families, parquet_filenames.pedigree
    )

    ParquetManager.variants_to_parquet_filename(
        iossifov2014_loader, parquet_filenames.variant
    )

    impala_genotype_storage.impala_load_study(
        study_id,
        variant_paths=[parquet_filenames.variant],
        pedigree_paths=[parquet_filenames.pedigree],
    )

    fvars = impala_genotype_storage.build_backend(
        GPFConfigParser._dict_to_namedtuple({"id": study_id}), genomes_db_2013
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
def vcf_variants_loader(
    vcf_loader_data, default_annotation_pipeline, genomes_db_2013
):
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
        conf = vcf_loader_data(path)

        families_loader = FamiliesLoader(conf.pedigree)
        families = families_loader.load()

        loader = VcfLoader(
            families, [conf.vcf], genomes_db_2013.get_genome(), params=params
        )
        assert loader is not None

        loader = AnnotationPipelineDecorator(
            loader, default_annotation_pipeline
        )

        return loader

    return builder


@pytest.fixture(scope="session")
def variants_vcf(vcf_variants_loader):
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

        loader = vcf_variants_loader(path, params=params)
        fvars = RawMemoryVariants([loader], loader.families)
        return fvars

    return builder


@pytest.fixture(scope="session")
def variants_mem():
    def builder(loader):
        fvars = RawMemoryVariants([loader], loader.families)
        return fvars

    return builder


@pytest.fixture(scope="session")
def annotation_pipeline_default_decorator(default_annotation_pipeline):
    def builder(variants_loader):
        decorator = AnnotationPipelineDecorator(
            variants_loader, default_annotation_pipeline
        )
        return decorator

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
def raw_dae(config_dae, genome_2013):
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
            genome=genome_2013,
        )
        return dae

    return builder


def pytest_addoption(parser):
    parser.addoption(
        "--reimport", action="store_true", default=False, help="force reimport"
    )


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
    storage_config = GPFConfigParser._dict_to_namedtuple(
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
            "hdfs": {"host": hdfs_host, "port": 8020, "base_dir": "/tmp"},
        }
    )

    return ImpalaGenotypeStorage(storage_config)


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

    annotation_pipeline = construct_import_annotation_pipeline(
        gpf_instance_2013
    )

    def fin():
        hdfs.delete(temp_dirname, recursive=True)

    request.addfinalizer(fin)

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

        for vcf in vcf_configs:
            print("importing vcf:", vcf.vcf)

            filename = os.path.basename(vcf.pedigree)
            study_id = os.path.splitext(filename)[0]

            (
                variant_table,
                pedigree_table,
            ) = impala_genotype_storage.study_tables(
                GPFConfigParser._dict_to_namedtuple({"id": study_id})
            )

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

            study_id = study_id_from_path(vcf.pedigree)
            study_temp_dirname = os.path.join(temp_dirname, study_id)

            families_loader = FamiliesLoader(vcf.pedigree)
            families = families_loader.load()
            genome = gpf_instance_2013.genomes_db.get_genome()

            loader = VcfLoader(
                families,
                [vcf.vcf],
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

            loader = AnnotationPipelineDecorator(loader, annotation_pipeline)

            impala_genotype_storage.simple_study_import(
                study_id,
                families_loader=families_loader,
                variant_loaders=[loader],
                output=study_temp_dirname,
                include_reference=True)

    build("backends/")
    return True


@pytest.fixture(scope="session")
def variants_impala(
    request, data_import, impala_genotype_storage, genomes_db_2013
):
    def builder(path):
        study_id = os.path.basename(path)
        fvars = impala_genotype_storage.build_backend(
            GPFConfigParser._dict_to_namedtuple({"id": study_id}),
            genomes_db_2013,
        )
        return fvars

    return builder


@pytest.fixture(scope="function")
def test_fixture():
    print("start")
    yield "works"
    print("end")


@pytest.fixture(scope="session")
def variants_db_fixture(fixtures_gpf_instance):
    return fixtures_gpf_instance._variants_db


@pytest.fixture(scope="session")
def calc_gene_sets(request, variants_db_fixture):
    genotype_data_names = ["f1_group", "f2_group", "f3_group"]
    for dgs in genotype_data_names:
        genotype_data = variants_db_fixture.get(dgs)
        assert genotype_data is not None

        DenovoGeneSetCollectionFactory.build_collection(genotype_data)

    def remove_gene_sets():
        for dgs in genotype_data_names:
            genotype_data = variants_db_fixture.get(dgs)
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


@pytest.fixture(scope="session")
def sv1():
    return SummaryVariant(
        [
            SummaryAllele("1", 11539, "T", None, 0, 0),
            SummaryAllele("1", 11539, "T", "TA", 0, 1),
            SummaryAllele("1", 11539, "T", "TG", 0, 2),
        ]
    )


@pytest.fixture(scope="session")
def svX1():
    return SummaryVariant(
        [
            SummaryAllele("X", 154931050, "T", None, 0, 0),
            SummaryAllele("X", 154931050, "T", "A", 0, 1),
            SummaryAllele("X", 154931050, "T", "G", 0, 2),
        ]
    )


@pytest.fixture(scope="session")
def svX2():
    return SummaryVariant(
        [
            SummaryAllele("X", 3_000_000, "C", None, 0, 0),
            SummaryAllele("X", 3_000_000, "C", "A", 0, 1),
            SummaryAllele("X", 3_000_000, "C", "A", 0, 2),
        ]
    )


@pytest.fixture
def fv1(fam1, sv1):
    def build(gt, best_st):
        return FamilyVariant(sv1, fam1, gt, best_st)

    return build


@pytest.fixture
def fvX1(fam1, svX1):
    def build(gt, best_st):
        return FamilyVariant(svX1, fam1, gt, best_st)

    return build


@pytest.fixture
def fvX2(fam1, svX2):
    def build(gt, best_st):
        return FamilyVariant(svX2, fam1, gt, best_st)

    return build
