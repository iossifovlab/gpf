import pytest

import os
import glob
import shutil
import tempfile

import pandas as pd
from io import StringIO

from box import Box
from dae.GenomesDB import GenomesDB

from dae.configuration.dae_config_parser import DAEConfigParser
from dae.gpf_instance.gpf_instance import GPFInstance, cached

from dae.annotation.annotation_pipeline import PipelineAnnotator

from dae.backends.raw.loader import AlleleFrequencyDecorator, \
    AnnotationPipelineDecorator
from dae.backends.raw.raw_variants import RawMemoryVariants

from dae.backends.dae.loader import DaeTransmittedLoader, DenovoLoader
from dae.backends.vcf.loader import VcfLoader

from dae.backends.import_commons import \
    construct_import_annotation_pipeline

from dae.pedigrees.family import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.utils.helpers import study_id_from_path

from dae.backends.impala.parquet_io import ParquetManager
from dae.backends.storage.impala_genotype_storage import ImpalaGenotypeStorage
from dae.gene.denovo_gene_set_config import DenovoGeneSetConfigParser
from dae.gene.denovo_gene_set_collection_factory import \
    DenovoGeneSetCollectionFactory


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'tests',
        path
    )


def get_global_dae_fixtures_dir():
    return relative_to_this_test_folder('fixtures')


@pytest.fixture(scope='session')
def global_dae_fixtures_dir():
    return get_global_dae_fixtures_dir()


@pytest.fixture(scope='session')
def default_dae_config(request):
    studies_dirname = tempfile.mkdtemp(
        prefix='studies_', suffix='_test')

    def fin():
        shutil.rmtree(studies_dirname)

    request.addfinalizer(fin)
    dae_config = DAEConfigParser.read_and_parse_file_configuration()
    dae_config.studies_db.dir = studies_dirname
    return dae_config


@pytest.fixture(scope='session')
def gpf_instance(default_dae_config):
    class GenomesDbInternal(GenomesDB):

        def get_gene_model_id(self, genome_id=None):
            return "RefSeq2013"

    class GPFInstanceInternal(GPFInstance):
        @property
        @cached
        def genomes_db(self):
            return GenomesDbInternal(
                default_dae_config.dae_data_dir,
                default_dae_config.genomes_db.conf_file
            )

    def build(work_dir=None, load_eagerly=False):
        return GPFInstanceInternal(
            work_dir=work_dir, load_eagerly=load_eagerly)

    return build


@pytest.fixture(scope='session')
def gpf_instance_2013(default_dae_config):

    class GenomesDb2013(GenomesDB):

        def get_gene_model_id(self, genome_id=None):
            return "RefSeq2013"

    class GPFInstance2013(GPFInstance):
        @property
        @cached
        def genomes_db(self):
            return GenomesDb2013(
                self.dae_config.dae_data_dir,
                self.dae_config.genomes_db.conf_file
            )

    return GPFInstance2013(dae_config=default_dae_config)


@pytest.fixture(scope='session')
def gene_models_2013(gpf_instance_2013):
    return gpf_instance_2013.genomes_db.get_gene_models("RefSeq2013")


@pytest.fixture(scope='session')
def genomes_db_2013(gpf_instance_2013):
    return gpf_instance_2013.genomes_db


@pytest.fixture(scope='session')
def genome_2013(gpf_instance_2013):
    return gpf_instance_2013.genomes_db.get_genome()


@pytest.fixture(scope='session')
def gpf_instance_2019(default_dae_config):

    class GenomesDb2019(GenomesDB):

        def get_gene_model_id(self, genome_id=None):
            return "RefSeq"

    class GPFInstance2019(GPFInstance):
        @property
        @cached
        def genomes_db(self):
            return GenomesDb2019(
                self.dae_config.dae_data_dir,
                self.dae_config.genomes_db.conf_file
            )

    return GPFInstance2019(dae_config=default_dae_config)


@pytest.fixture(scope='session')
def gene_models_2019(gpf_instance_2019):
    return gpf_instance_2019.genomes_db.get_gene_models("RefSeq")


@pytest.fixture(scope='session')
def genomes_db_2019(gpf_instance_2019):
    return gpf_instance_2019.genomes_db


@pytest.fixture
def result_df():
    def build(data):
        infile = StringIO(str(data))
        df = pd.read_csv(infile, sep='\t')
        return df
    return build


@pytest.fixture
def temp_dirname(request):
    dirname = tempfile.mkdtemp(suffix='_data', prefix='variants_')

    def fin():
        shutil.rmtree(dirname)

    request.addfinalizer(fin)
    return dirname


@pytest.fixture
def temp_filename(request):
    dirname = tempfile.mkdtemp(suffix='_eff', prefix='variants_')

    def fin():
        shutil.rmtree(dirname)

    request.addfinalizer(fin)
    output = os.path.join(
        dirname,
        'temp_filename.tmp'
    )
    return output


@pytest.fixture(scope='session')
def fixture_dirname(request):
    def builder(relpath):
        return relative_to_this_test_folder(
            os.path.join('fixtures', relpath))
    return builder


@pytest.fixture(scope='session')
def annotation_pipeline_config():
    filename = relative_to_this_test_folder(
        'fixtures/annotation_pipeline/import_annotation.conf')
    return filename


@pytest.fixture(scope='session')
def annotation_pipeline_default_config(default_dae_config):
    return default_dae_config.annotation.conf_file


@pytest.fixture(scope='session')
def default_annotation_pipeline(
        default_dae_config, genomes_db_2013):
    filename = default_dae_config.annotation.conf_file

    options = Box({
            'default_arguments': None,
            'vcf': True,
            'r': 'reference',
            'a': 'alternative',
            'c': 'chrom',
            'p': 'position',
        },
        default_box=True,
        default_box_attr=None)

    pipeline = PipelineAnnotator.build(
        options, filename, '.', genomes_db_2013,
        defaults={})

    return pipeline


@pytest.fixture(scope='session')
def annotation_scores_dirname():
    filename = relative_to_this_test_folder(
        'fixtures/annotation_pipeline/')
    return filename


@pytest.fixture(scope='session')
def annotation_pipeline_vcf(genomes_db_2013):
    filename = relative_to_this_test_folder(
        'fixtures/annotation_pipeline/import_annotation.conf')

    options = Box({
            'default_arguments': None,
            'vcf': True,
            # 'mode': 'overwrite',
        },
        default_box=True,
        default_box_attr=None)

    work_dir = relative_to_this_test_folder('fixtures/')

    pipeline = PipelineAnnotator.build(
        options, filename, work_dir, genomes_db_2013,
        defaults={'values': {
            'scores_dirname': relative_to_this_test_folder(
                'fixtures/annotation_pipeline/')
        }})
    return pipeline


@pytest.fixture(scope='session')
def annotation_pipeline_internal(genomes_db_2013):
    assert genomes_db_2013 is not None
    assert genomes_db_2013.get_gene_model_id() == "RefSeq2013"
    filename = relative_to_this_test_folder(
        'fixtures/annotation_pipeline/import_annotation.conf')

    options = Box({
            'default_arguments': None,
            'vcf': True,
            'c': 'chrom',
            'p': 'position',
            'r': 'reference',
            'a': 'alternative',
        },
        default_box=True,
        default_box_attr=None)

    work_dir = relative_to_this_test_folder('fixtures/')

    pipeline = PipelineAnnotator.build(
        options, filename, work_dir, genomes_db_2013,
        defaults={'values': {
            'scores_dirname': relative_to_this_test_folder(
                'fixtures/annotation_pipeline/')
        }})
    return pipeline


def from_prefix_denovo(prefix):
    denovo_filename = '{}.txt'.format(prefix)
    family_filename = "{}_families.ped".format(prefix)

    conf = {
        'denovo': {
            'denovo_filename': denovo_filename,
            'family_filename': family_filename,
        }
    }
    return Box(conf, default_box=True)


def from_prefix_vcf(prefix):
    vcf_filename = '{}.vcf'.format(prefix)
    if not os.path.exists(vcf_filename):
        vcf_filename = '{}.vcf.gz'.format(prefix)

    conf = {
        'pedigree': '{}.ped'.format(prefix),
        'vcf': vcf_filename,
        'annotation': '{}-eff.txt'.format(prefix),
        'prefix': prefix
    }
    return Box(conf, default_box=True)


@pytest.fixture
def dae_denovo_config():
    fullpath = relative_to_this_test_folder(
        'fixtures/dae_denovo/denovo'
    )
    config = from_prefix_denovo(fullpath)
    return config.denovo


@pytest.fixture
def dae_denovo(
        dae_denovo_config, genome_2013, annotation_pipeline_internal):

    families_loader = FamiliesLoader(
        dae_denovo_config.family_filename,
        params={'ped_file_format': 'simple'})
    families = families_loader.load()

    variants_loader = DenovoLoader(
        families, dae_denovo_config.denovo_filename,
        genome_2013)

    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal)
    fvars = RawMemoryVariants([variants_loader])
    return fvars


def from_prefix_dae(prefix):
    summary_filename = '{}.txt.gz'.format(prefix)
    toomany_filename = '{}-TOOMANY.txt.gz'.format(prefix)
    family_filename = "{}.families.txt".format(prefix)

    conf = {
        'dae': {
            'summary_filename': summary_filename,
            'toomany_filename': toomany_filename,
            'family_filename': family_filename,
        }
    }
    return Box(conf, default_box=True)


@pytest.fixture
def dae_transmitted_config():
    fullpath = relative_to_this_test_folder(
        'fixtures/dae_transmitted/transmission'
    )
    config = from_prefix_dae(fullpath)
    return config.dae


@pytest.fixture
def dae_transmitted(
        dae_transmitted_config, genome_2013, annotation_pipeline_internal):

    ped_df = FamiliesLoader.load_simple_family_file(
        dae_transmitted_config.family_filename
    )
    families = FamiliesData.from_pedigree_df(ped_df)

    variants_loader = DaeTransmittedLoader(
        families,
        dae_transmitted_config.summary_filename,
        dae_transmitted_config.toomany_filename,
        genome=genome_2013,
        region=None,
    )
    variants_loader = AnnotationPipelineDecorator(
        variants_loader,
        annotation_pipeline_internal
    )

    return variants_loader


@pytest.fixture(scope='session')
def dae_iossifov2014_config():
    fullpath = relative_to_this_test_folder(
        'fixtures/dae_iossifov2014/iossifov2014'
    )
    config = from_prefix_denovo(fullpath)
    return config.denovo


@pytest.fixture(scope='session')
def iossifov2014_loader(
        dae_iossifov2014_config, genome_2013,
        annotation_pipeline_internal):
    config = dae_iossifov2014_config

    families_loader = FamiliesLoader(config.family_filename)
    families = families_loader.load()

    variants_loader = DenovoLoader(
        families, config.denovo_filename, genome_2013)

    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal)

    return variants_loader


@pytest.fixture(scope='session')
def iossifov2014_raw_denovo(iossifov2014_loader):

    fvars = RawMemoryVariants([iossifov2014_loader])

    return fvars


@pytest.fixture(scope='session')
def iossifov2014_impala(
        request, iossifov2014_loader, genomes_db_2013,
        test_hdfs, impala_genotype_storage, parquet_manager):

    temp_dirname = test_hdfs.tempdir(prefix='variants_', suffix='_data')
    test_hdfs.mkdir(temp_dirname)

    study_id = 'iossifov_wd2014_test'
    parquet_filenames = ParquetManager.build_parquet_filenames(
        temp_dirname, bucket_index=0, study_id=study_id
    )

    assert parquet_filenames is not None
    print(parquet_filenames)

    ParquetManager.pedigree_to_parquet(
        iossifov2014_loader.families, parquet_filenames.pedigree)

    ParquetManager.variants_to_parquet(
        iossifov2014_loader, parquet_filenames.variant)

    impala_genotype_storage.impala_load_study(
        study_id,
        variant_paths=[parquet_filenames.variant],
        pedigree_paths=[parquet_filenames.pedigree],
    )

    fvars = impala_genotype_storage.build_backend(
        Box({'id': study_id}, default_box=True),
        genomes_db_2013)
    return fvars


@pytest.fixture(scope='session')
def vcf_loader_data():
    def builder(path):
        if os.path.isabs(path):
            prefix = path
        else:
            prefix = os.path.join(
                relative_to_this_test_folder('fixtures'), path)
        conf = from_prefix_vcf(prefix)
        return conf
    return builder


@pytest.fixture(scope='session')
def vcf_variants_loader(vcf_loader_data, default_annotation_pipeline):
    def builder(
        path, params={
            'include_reference_genotypes': True,
            'include_unknown_family_genotypes': True,
            'include_unknown_person_genotypes': True
            }):
        conf = vcf_loader_data(path)

        ped_df = FamiliesLoader.flexible_pedigree_read(conf.pedigree)
        families = FamiliesData.from_pedigree_df(ped_df)

        loader = VcfLoader(families, conf.vcf, params=params)
        assert loader is not None

        loader = AlleleFrequencyDecorator(loader)
        loader = AnnotationPipelineDecorator(
            loader, default_annotation_pipeline)

        return loader
    return builder


@pytest.fixture(scope='session')
def variants_vcf(vcf_variants_loader):
    def builder(path):
        loader = vcf_variants_loader(path)

        fvars = RawMemoryVariants([loader])
        return fvars

    return builder


@pytest.fixture(scope='session')
def variants_mem():
    def builder(loader):
        fvars = RawMemoryVariants([loader])
        return fvars

    return builder


@pytest.fixture(scope='session')
def annotation_pipeline_default_decorator(default_annotation_pipeline):
    def builder(variants_loader):
        decorator = AnnotationPipelineDecorator(
            variants_loader, default_annotation_pipeline)
        return decorator

    return builder


@pytest.fixture
def variants_implementations(
        variants_impala, variants_vcf):
    impls = {
        'variants_impala': variants_impala,
        'variants_vcf': variants_vcf
    }
    return impls


@pytest.fixture
def variants_impl(variants_implementations):
    return lambda impl_name: variants_implementations[impl_name]


@pytest.fixture(scope='session')
def config_dae():
    def builder(path):
        fullpath = relative_to_this_test_folder(
            os.path.join('fixtures', path))
        config = from_prefix_dae(fullpath)
        return config
    return builder


@pytest.fixture(scope='session')
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
            genome=genome_2013)
        return dae
    return builder


def impala_test_dbname():
    return 'impala_test_db'


def pytest_addoption(parser):
    parser.addoption(
        '--reimport', action='store_true', default=False,
        help='force reimport'
    )


@pytest.fixture(scope='session')
def reimport(request):
    return bool(request.config.getoption('--reimport'))


@pytest.fixture(scope='session')
def hdfs_host():
    return os.environ.get('DAE_HDFS_HOST', '127.0.0.1')


@pytest.fixture(scope='session')
def impala_host():
    return os.environ.get('DAE_IMPALA_HOST', '127.0.0.1')


# Impala backend
@pytest.fixture(scope='session')
def test_hdfs(request, hdfs_host):
    from dae.backends.impala.hdfs_helpers import HdfsHelpers
    hdfs = HdfsHelpers(hdfs_host, 8020)
    return hdfs


@pytest.fixture(scope='session')
def test_impala_helpers(request, impala_host):
    from dae.backends.impala.impala_helpers import ImpalaHelpers
    helpers = ImpalaHelpers(impala_host=impala_host, impala_port=21050)

    return helpers


@pytest.fixture(scope='session')
def impala_genotype_storage(hdfs_host, impala_host):
    storage_config = Box({
        'id': 'impala_test_storage',
        'type': 'impala',
        'impala': {
            'host': impala_host,
            'port': 21050,
            'db': impala_test_dbname(),
        },
        'hdfs': {
            'host': hdfs_host,
            'port': 8020,
            'base_dir': '/tmp'
        }
    })

    return ImpalaGenotypeStorage(storage_config)


@pytest.fixture(scope='session')
def parquet_manager(default_dae_config):
    return ParquetManager(default_dae_config.studies_db.dir)


def collect_vcf(dirname):
    result = []
    pattern = os.path.join(dirname, '*.vcf')
    for filename in glob.glob(pattern):
        prefix = os.path.splitext(filename)[0]
        vcf_config = from_prefix_vcf(prefix)
        result.append(vcf_config)
    return result


DATA_IMPORT_COUNT = 0


@pytest.fixture(scope='session')
def data_import(
        request, test_hdfs, test_impala_helpers, parquet_manager,
        impala_genotype_storage, reimport, default_dae_config,
        genomes_db_2013):

    global DATA_IMPORT_COUNT
    DATA_IMPORT_COUNT += 1

    assert DATA_IMPORT_COUNT == 1

    temp_dirname = test_hdfs.tempdir(prefix='variants_', suffix='_data')
    test_hdfs.mkdir(temp_dirname)

    annotation_pipeline = \
        construct_import_annotation_pipeline(
            default_dae_config,
            genomes_db_2013)

    def fin():
        test_hdfs.delete(temp_dirname, recursive=True)
    request.addfinalizer(fin)

    def build(dirname):

        if not test_impala_helpers.check_database(impala_test_dbname()):
            test_impala_helpers.create_database(impala_test_dbname())

        vcfdirname = relative_to_this_test_folder(
            os.path.join('fixtures', dirname))
        vcf_configs = collect_vcf(vcfdirname)

        for vcf in vcf_configs:
            print('importing vcf:', vcf.vcf)

            filename = os.path.basename(vcf.pedigree)
            study_id = os.path.splitext(filename)[0]

            variant_table, pedigree_table = impala_genotype_storage. \
                study_tables(Box({'id': study_id}, default_box=True))

            if not reimport and \
                    test_impala_helpers.check_table(
                        impala_test_dbname(), variant_table) and \
                    test_impala_helpers.check_table(
                        impala_test_dbname(), pedigree_table):
                continue

            study_id = study_id_from_path(vcf.pedigree)
            study_temp_dirname = os.path.join(temp_dirname, study_id)

            families_loader = FamiliesLoader(vcf.pedigree)
            families = families_loader.load()

            loader = VcfLoader(
                families, vcf.vcf, regions=None,
                params={
                    'include_reference_genotypes': True,
                    'include_unknown_family_genotypes': True,
                    'include_unknown_person_genotypes': True
                })

            loader = AlleleFrequencyDecorator(loader)
            loader = AnnotationPipelineDecorator(loader, annotation_pipeline)

            impala_genotype_storage.simple_study_import(
                study_id,
                families_loader=families_loader,
                variant_loaders=[loader],
                output=study_temp_dirname
            )

    build('backends/')
    return True


@pytest.fixture(scope='session')
def variants_impala(
        request, data_import, impala_genotype_storage,
        genomes_db_2013):

    def builder(path):
        study_id = os.path.basename(path)
        fvars = impala_genotype_storage.build_backend(
            Box({'id': study_id}, default_box=True),
            genomes_db_2013)
        return fvars

    return builder


@pytest.fixture
def vcf_import_config():
    fullpath = relative_to_this_test_folder(
        'fixtures/vcf_import/effects_trio'
    )
    config = from_prefix_vcf(fullpath)
    return config


@pytest.fixture(scope='session')
def parquet_partition_configuration():
    filename = relative_to_this_test_folder(
        'fixtures/backends/example_partition_configuration.conf')
    return filename


@pytest.fixture(scope='session')
def sample_parquet_partition_root():
    return relative_to_this_test_folder('fixtures/backends/test_partition')


@pytest.fixture(scope='function')
def test_fixture():
    print('start')
    yield 'works'
    print('end')


# @pytest.fixture(scope='session')
# def gpf_instance(mock_genomes_db, global_dae_fixtures_dir):
#     return GPFInstance(work_dir=global_dae_fixtures_dir)


@pytest.fixture(scope='session')
def variants_db_fixture(gpf_instance):
    return gpf_instance._variants_db


@pytest.fixture(scope='session')
def calc_gene_sets(request, variants_db_fixture):
    genotype_data_names = ['f1_group', 'f2_group', 'f3_group']
    for dgs in genotype_data_names:
        genotype_data = variants_db_fixture.get(dgs)
        DenovoGeneSetCollectionFactory.build_collection(genotype_data)

    print("PRECALCULATION COMPLETE")

    def remove_gene_sets():
        for dgs in genotype_data_names:
            genotype_data = variants_db_fixture.get(dgs)
            config = DenovoGeneSetConfigParser.parse(genotype_data.config)
            os.remove(DenovoGeneSetConfigParser.denovo_gene_set_cache_file(
                config, 'phenotype')
            )
    request.addfinalizer(remove_gene_sets)
