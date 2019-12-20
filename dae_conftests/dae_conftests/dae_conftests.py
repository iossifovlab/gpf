import pytest
from _pytest.monkeypatch import MonkeyPatch

import os
import glob
import shutil
import tempfile

import pandas as pd
from io import StringIO

from box import Box
from dae.configuration.dae_config_parser import DAEConfigParser
from dae.gpf_instance.gpf_instance import GPFInstance

from dae.annotation.annotation_pipeline import PipelineAnnotator

from dae.backends.raw.loader import AlleleFrequencyDecorator, \
    AnnotationPipelineDecorator
from dae.backends.raw.raw_variants import RawMemoryVariants

from dae.backends.dae.loader import DaeTransmittedLoader, DenovoLoader
from dae.backends.vcf.loader import VcfLoader

from dae.backends.import_commons import \
    construct_import_annotation_pipeline

from dae.pedigrees.family import PedigreeReader
from dae.pedigrees.family import FamiliesData, FamiliesLoader
from dae.utils.helpers import study_id_from_path

from dae.backends.impala.parquet_io import ParquetManager
from dae.backends.storage.impala_genotype_storage import ImpalaGenotypeStorage


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'tests',
        path
    )


def get_global_dae_fixtures_dir():
    print('Dar-jee says:', relative_to_this_test_folder('fixtures'))
    return relative_to_this_test_folder('fixtures')


@pytest.fixture(scope='session')
def global_dae_fixtures_dir():
    return get_global_dae_fixtures_dir()


@pytest.fixture(scope='session')
def monkeysession(request):
    mp = MonkeyPatch()
    request.addfinalizer(mp.undo)
    return mp


@pytest.fixture(scope='session')
def default_dae_config(request):
    dirname = tempfile.mkdtemp(suffix='_test', prefix='studies_')

    def fin():
        shutil.rmtree(dirname)

    request.addfinalizer(fin)
    dae_config = DAEConfigParser.read_and_parse_file_configuration()
    dae_config.studies_db.dir = dirname

    return dae_config


@pytest.fixture(scope='session')
def default_gpf_instance(default_dae_config):
    return GPFInstance(dae_config=default_dae_config)


@pytest.fixture(scope='session')
def dae_config_fixture(default_gpf_instance):
    return default_gpf_instance.dae_config


@pytest.fixture(scope='session')
def genomes_db(default_gpf_instance):
    return default_gpf_instance.genomes_db


@pytest.fixture(scope='session')
def default_genome(default_gpf_instance):
    return default_gpf_instance.genomes_db.get_genome()


@pytest.fixture(scope='session')
def default_gene_models(default_gpf_instance):
    return default_gpf_instance.genomes_db.get_gene_models("RefSeq2013")


@pytest.fixture(scope='session')
def mock_genomes_db(monkeysession, default_gene_models, default_genome):

    def fake_init(self, dae_dir, conf_file=None):
        self.dae_dir = None
        self.config = None

    monkeysession.setattr(
        'dae.GenomesDB.GenomesDB.__init__', fake_init
    )

    monkeysession.setattr(
        'dae.GenomesDB.GenomesDB.get_genome',
        lambda self: default_genome
    )
    monkeysession.setattr(
        'dae.GenomesDB.GenomesDB.get_genome_from_file',
        lambda self, _=None: default_genome
    )
    monkeysession.setattr(
        'dae.GenomesDB.GenomesDB.get_gene_models',
        lambda self, _=None: default_gene_models
    )
    monkeysession.setattr(
        'dae.GenomesDB.GenomesDB.get_genome_file',
        lambda self, _=None:
            './genomes/GATK_ResourceBundle_5777_b37_phiX174/chrAll.fa'
    )
    monkeysession.setattr(
        'dae.GenomesDB.GenomesDB.get_gene_model_id',
        lambda self: 'RefSeq2013'
    )


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
def annotation_pipeline_default_config(dae_config_fixture):
    return dae_config_fixture.annotation.conf_file


@pytest.fixture(scope='session')
def default_annotation_pipeline(
        default_dae_config, genomes_db):
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
        options, filename, '.', genomes_db,
        defaults={})

    return pipeline


@pytest.fixture(scope='session')
def annotation_scores_dirname():
    filename = relative_to_this_test_folder(
        'fixtures/annotation_pipeline/')
    return filename


@pytest.fixture(scope='session')
def annotation_pipeline_vcf(genomes_db):
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
        options, filename, work_dir, genomes_db,
        defaults={'values': {
            'scores_dirname': relative_to_this_test_folder(
                'fixtures/annotation_pipeline/')
        }})
    return pipeline


@pytest.fixture(scope='session')
def annotation_pipeline_internal(genomes_db):
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
        options, filename, work_dir, genomes_db,
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
        dae_denovo_config, default_genome, annotation_pipeline_internal):

    families_loader = FamiliesLoader(
        dae_denovo_config.family_filename,
        params={'ped_file_format': 'simple'})

    variants_loader = DenovoLoader(
        families_loader.families, dae_denovo_config.denovo_filename,
        default_genome)

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
        dae_transmitted_config, default_genome, annotation_pipeline_internal):

    ped_df = PedigreeReader.load_simple_family_file(
        dae_transmitted_config.family_filename
    )
    families = FamiliesData.from_pedigree_df(ped_df)

    variants_loader = DaeTransmittedLoader(
        families,
        dae_transmitted_config.summary_filename,
        dae_transmitted_config.toomany_filename,
        genome=default_genome,
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
        dae_iossifov2014_config, default_genome,
        annotation_pipeline_internal):
    config = dae_iossifov2014_config

    families_loader = FamiliesLoader(config.family_filename)

    variants_loader = DenovoLoader(
        families_loader.families, config.denovo_filename, default_genome)

    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal)

    return variants_loader


@pytest.fixture(scope='session')
def iossifov2014_raw_denovo(iossifov2014_loader):

    fvars = RawMemoryVariants([iossifov2014_loader])

    return fvars


@pytest.fixture(scope='session')
def iossifov2014_impala(
        request, iossifov2014_loader, genomes_db,
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
        iossifov2014_loader, parquet_filenames.pedigree)

    ParquetManager.variants_to_parquet(
        iossifov2014_loader, parquet_filenames.variant)

    impala_genotype_storage.impala_load_study(
        study_id,
        variant_paths=[parquet_filenames.variant],
        pedigree_paths=[parquet_filenames.pedigree],
    )

    fvars = impala_genotype_storage.build_backend(
        Box({'id': study_id}, default_box=True),
        genomes_db)
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

        ped_df = PedigreeReader.flexible_pedigree_read(conf.pedigree)
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
def raw_dae(config_dae, default_genome):
    def builder(path, region=None):
        config = config_dae(path)

        ped_df = PedigreeReader.load_simple_family_file(
            dae_transmitted_config.family_filename
        )

        dae = DaeTransmittedLoader(
            config.dae.summary_filename,
            config.dae.toomany_filename,
            ped_df,
            region=region,
            genome=default_genome)
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
def parquet_manager(dae_config_fixture):
    return ParquetManager(dae_config_fixture.studies_db.dir)


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
        impala_genotype_storage, reimport, dae_config_fixture, genomes_db):

    global DATA_IMPORT_COUNT
    DATA_IMPORT_COUNT += 1

    assert DATA_IMPORT_COUNT == 1

    temp_dirname = test_hdfs.tempdir(prefix='variants_', suffix='_data')
    test_hdfs.mkdir(temp_dirname)

    annotation_pipeline = \
        construct_import_annotation_pipeline(dae_config_fixture, genomes_db)

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
            loader = VcfLoader(
                families_loader.families, vcf.vcf, regions=None,
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
def variants_impala(request, data_import, impala_genotype_storage, genomes_db):

    def builder(path):
        study_id = os.path.basename(path)
        fvars = impala_genotype_storage.build_backend(
            Box({'id': study_id}, default_box=True),
            genomes_db)
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
