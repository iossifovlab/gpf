import pytest

import os
import glob
import shutil
import tempfile

import pandas as pd
from io import StringIO

from box import Box

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.annotation.annotation_pipeline import PipelineAnnotator

from dae.backends.configure import Configure
from dae.backends.raw.loader import AlleleFrequencyDecorator
from dae.backends.raw.raw_variants import RawMemoryVariants

from dae.backends.dae.loader import RawDaeLoader
from dae.backends.dae.raw_dae import RawDAE

from dae.backends.vcf.loader import RawVcfLoader, VcfLoader

from dae.backends.import_commons import \
    construct_import_annotation_pipeline

from dae.pedigrees.pedigree_reader import PedigreeReader
from dae.pedigrees.family import FamiliesData
from dae.utils.helpers import study_id_from_path
from dae.backends.import_commons import variants2parquet

from dae.backends.impala.parquet_io import ParquetManager
from dae.backends.storage.impala_genotype_storage import ImpalaGenotypeStorage


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'tests',
        path
    )


@pytest.fixture(scope='session')
def global_gpf_instance():
    return GPFInstance()


@pytest.fixture(scope='session')
def default_dae_config(global_gpf_instance):
    return global_gpf_instance.dae_config


@pytest.fixture(scope='session')
def dae_config_fixture(global_gpf_instance):
    return global_gpf_instance.dae_config


@pytest.fixture(scope='session')
def genomes_db(global_gpf_instance):
    return global_gpf_instance.genomes_db


@pytest.fixture(scope='session')
def default_genome(global_gpf_instance):
    return global_gpf_instance.genomes_db.get_genome()


@pytest.fixture(scope='session')
def default_gene_models(global_gpf_instance):
    return global_gpf_instance.genomes_db.get_gene_models()


@pytest.fixture(scope='function')
def mock_genomes_db(mocker, default_gene_models, default_genome):
    # genome = mocker.Mock()
    # genome.getSequence = lambda _, start, end: 'A' * (end - start + 1)

    mocker.patch(
        'dae.GenomesDB.GenomesDB.__init__', return_value=None
    )

    mocker.patch(
        'dae.GenomesDB.GenomesDB.get_genome',
        return_value=default_genome
    )
    mocker.patch(
        'dae.GenomesDB.GenomesDB.get_genome_from_file',
        return_value=default_genome
    )
    mocker.patch(
        'dae.GenomesDB.GenomesDB.get_gene_models',
        return_value=default_gene_models
    )
    mocker.patch(
        'dae.GenomesDB.GenomesDB.get_genome_file',
        return_value='./genomes/GATK_ResourceBundle_5777_b37_phiX174/chrAll.fa'
    )
    mocker.patch(
        'dae.GenomesDB.GenomesDB.get_gene_model_id',
        return_value='RefSeq2013'
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


@pytest.fixture
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


@pytest.fixture
def dae_denovo_config():
    fullpath = relative_to_this_test_folder(
        'fixtures/dae_denovo/denovo'
    )
    config = Configure.from_prefix_denovo(fullpath)
    return config.denovo


@pytest.fixture
def dae_denovo(
        dae_denovo_config, default_genome, annotation_pipeline_internal):

    fvars = RawDaeLoader.load_raw_denovo_variants(
        dae_denovo_config.family_filename,
        dae_denovo_config.denovo_filename,
        None,
        default_genome,
        family_format='simple'
    )
    fvars.annotate(annotation_pipeline_internal)
    return fvars


@pytest.fixture
def dae_transmitted_config():
    fullpath = relative_to_this_test_folder(
        'fixtures/dae_transmitted/transmission'
    )
    config = Configure.from_prefix_dae(fullpath)
    return config.dae


@pytest.fixture
def dae_transmitted(
        dae_transmitted_config, default_genome, annotation_pipeline_internal):

    ped_df = PedigreeReader.load_simple_family_file(
        dae_transmitted_config.family_filename
    )
    families = FamiliesData.from_pedigree_df(ped_df)

    transmitted = RawDAE(
        families,
        dae_transmitted_config.summary_filename,
        dae_transmitted_config.toomany_filename,
        genome=default_genome,
        region=None,
    )

    return transmitted


@pytest.fixture(scope='session')
def dae_iossifov2014_config():
    fullpath = relative_to_this_test_folder(
        'fixtures/dae_iossifov2014/iossifov2014'
    )
    config = Configure.from_prefix_denovo(fullpath)
    return config.denovo


@pytest.fixture(scope='session')
def iossifov2014_raw_denovo(
        dae_iossifov2014_config, default_genome,
        annotation_pipeline_internal):
    config = dae_iossifov2014_config
    fvars = RawDaeLoader.load_raw_denovo_variants(
        config.family_filename,
        config.denovo_filename,
        None,
        default_genome,
        family_format='simple'
    )
    fvars.annotate(annotation_pipeline_internal)
    fvars.annotate(annotation_pipeline_internal)
    return fvars


@pytest.fixture(scope='session')
def iossifov2014_impala(
        request, iossifov2014_raw_denovo, genomes_db,
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
        iossifov2014_raw_denovo, parquet_filenames.pedigree)

    ParquetManager.variants_to_parquet(
        iossifov2014_raw_denovo, parquet_filenames.variant)

    impala_genotype_storage.impala_load_study(
        study_id,
        parquet_filenames.pedigree,
        parquet_filenames.variant
    )

    fvars = impala_genotype_storage.build_backend(
        impala_genotype_storage.default_study_config(study_id),
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
        conf = Configure.from_prefix_vcf(prefix).vcf
        return conf
    return builder


@pytest.fixture(scope='session')
def variants_vcf(genomes_db, default_annotation_pipeline):
    def builder(path):
        if os.path.isabs(path):
            prefix = path
        else:
            prefix = os.path.join(
                relative_to_this_test_folder('fixtures'), path)
        print(prefix)
        conf = Configure.from_prefix_vcf(prefix)
        print(conf)

        ped_df = PedigreeReader.flexible_pedigree_read(conf.vcf.pedigree)
        fvars = RawVcfLoader.load_and_annotate_raw_vcf_variants(
            ped_df, conf.vcf.vcf, default_annotation_pipeline
        )

        return fvars
    return builder


@pytest.fixture(scope='session')
def variants_mem(vcf_loader_data):
    def builder(path):
        conf = vcf_loader_data(path)

        ped_df = PedigreeReader.flexible_pedigree_read(conf.pedigree)
        families = FamiliesData.from_pedigree_df(ped_df)

        loader = VcfLoader(families, conf.vcf)
        assert loader is not None

        loader = AlleleFrequencyDecorator(loader)
        fvars = RawMemoryVariants(loader)
        return fvars

    return builder


@pytest.fixture
def variants_implementations(
        variants_vcf, variants_impala, variants_mem):
    impls = {
        'variants_vcf': variants_vcf,
        'variants_impala': variants_impala,
        'variants_mem': variants_mem
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
        config = Configure.from_prefix_dae(fullpath)
        return config
    return builder


@pytest.fixture(scope='session')
def raw_dae(config_dae, default_genome):
    def builder(path, region=None):
        config = config_dae(path)

        ped_df = PedigreeReader.load_simple_family_file(
            dae_transmitted_config.family_filename
        )

        dae = RawDAE(
            config.dae.summary_filename,
            config.dae.toomany_filename,
            ped_df,
            region=region,
            genome=default_genome,
            annotator=None)
        return dae
    return builder


@pytest.fixture(scope='session')
def config_denovo():
    def builder(path):
        fullpath = relative_to_this_test_folder(
            os.path.join('fixtures', path))
        config = Configure.from_prefix_denovo(fullpath)
        return config.denovo
    return builder


@pytest.fixture(scope='session')
def raw_denovo(config_denovo, default_genome):
    def builder(path):
        config = config_denovo(path)

        fvars = RawDaeLoader.load_raw_denovo_variants(
            config.family_filename,
            config.denovo_filename,
            None,
            default_genome,
            family_format='simple'
        )

        return fvars
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
        vcf_config = Configure.from_prefix_vcf(prefix).vcf
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

            impala = impala_genotype_storage._impala_storage_config(study_id)
            if not reimport and \
                    test_impala_helpers.check_table(
                        impala_test_dbname(), impala.tables.variant) and \
                    test_impala_helpers.check_table(
                        impala_test_dbname(), impala.tables.pedigree):
                continue

            study_id = study_id_from_path(vcf.pedigree)
            study_temp_dirname = os.path.join(temp_dirname, study_id)

            fvars = RawVcfLoader.load_and_annotate_raw_vcf_variants(
                vcf.pedigree, vcf.vcf, annotation_pipeline
            )
            parquet_filenames = variants2parquet(
                study_id, fvars,
                output=study_temp_dirname,
                bucket_index=0,
                include_reference=True,
                include_unknown=True
            )

            impala_genotype_storage.impala_load_study(
                study_id,
                parquet_filenames.pedigree,
                parquet_filenames.variant
            )

    build('backends/')
    return True


@pytest.fixture(scope='session')
def variants_impala(request, data_import, impala_genotype_storage, genomes_db):

    def builder(path):
        study_id = os.path.basename(path)
        fvars = impala_genotype_storage.build_backend(
            impala_genotype_storage.default_study_config(study_id),
            genomes_db)
        return fvars

    return builder


@pytest.fixture
def vcf_import_config():
    fullpath = relative_to_this_test_folder(
        'fixtures/vcf_import/effects_trio'
    )
    config = Configure.from_prefix_vcf(fullpath)
    return config.vcf
