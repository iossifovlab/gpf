
import os
import pytest
import shutil
import tempfile
import glob

import pandas as pd
from io import StringIO

from box import Box

from dae.configuration.configuration import DAEConfig

from dae.annotation.annotation_pipeline import PipelineAnnotator

from dae.backends.configure import Configure
from dae.backends.dae.raw_dae import RawDAE, RawDenovo
from dae.backends.vcf.raw_vcf import RawFamilyVariants
from dae.backends.vcf.annotate_allele_frequencies import \
    VcfAlleleFrequencyAnnotator

from dae.backends.import_commons import \
    construct_import_annotation_pipeline
from dae.tools.vcf2parquet import import_vcf


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "tests",
        path
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
        'annotation.tmp'
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
        "fixtures/annotation_pipeline/import_annotation.conf")
    return filename


@pytest.fixture(scope='session')
def annotation_pipeline_default_config():
    dae_config = DAEConfig.read_and_parse_file_configuration()
    return dae_config.annotation.conf_file


@pytest.fixture(scope='session')
def annotation_scores_dirname():
    filename = relative_to_this_test_folder(
        "fixtures/annotation_pipeline/")
    return filename


@pytest.fixture(scope='session')
def annotation_pipeline_vcf():
    filename = relative_to_this_test_folder(
        "fixtures/annotation_pipeline/import_annotation.conf")

    options = Box({
            "default_arguments": None,
            "vcf": True,
            # "mode": "overwrite",
        },
        default_box=True,
        default_box_attr=None)

    pipeline = PipelineAnnotator.build(
        options, filename,
        defaults={
            "scores_dirname": relative_to_this_test_folder(
                "fixtures/annotation_pipeline/")
        })
    return pipeline


@pytest.fixture(scope='session')
def annotation_pipeline_internal():
    filename = relative_to_this_test_folder(
        "fixtures/annotation_pipeline/import_annotation.conf")

    options = Box({
            "default_arguments": None,
            "vcf": True,
            'c': 'chrom',
            'p': 'position',
            'r': 'reference',
            'a': 'alternative',
        },
        default_box=True,
        default_box_attr=None)

    pipeline = PipelineAnnotator.build(
        options, filename,
        defaults={
            "scores_dirname": relative_to_this_test_folder(
                "fixtures/annotation_pipeline/")
        })
    return pipeline


@pytest.fixture(scope='session')
def default_genome():
    from dae.DAE import genomesDB
    genome = genomesDB.get_genome()  # @UndefinedVariable
    return genome


@pytest.fixture(scope='session')
def default_gene_models():
    from dae.DAE import genomesDB
    gene_models = genomesDB.get_gene_models("RefSeq2013")
    return gene_models


@pytest.fixture
def dae_denovo_config():
    fullpath = relative_to_this_test_folder(
        "fixtures/dae_denovo/denovo"
    )
    config = Configure.from_prefix_denovo(fullpath)
    return config.denovo


@pytest.fixture
def dae_denovo(
        dae_denovo_config, default_genome, annotation_pipeline_internal):
    denovo = RawDenovo(
        dae_denovo_config.denovo_filename,
        dae_denovo_config.family_filename,
        genome=default_genome,
        annotator=annotation_pipeline_internal)
    denovo.load_simple_families()

    return denovo


@pytest.fixture
def dae_transmitted_config():
    fullpath = relative_to_this_test_folder(
        "fixtures/dae_transmitted/transmission"
    )
    config = Configure.from_prefix_dae(fullpath)
    return config.dae


@pytest.fixture
def dae_transmitted(
        dae_transmitted_config, default_genome, annotation_pipeline_internal):
    denovo = RawDAE(
        dae_transmitted_config.summary_filename,
        dae_transmitted_config.toomany_filename,
        dae_transmitted_config.family_filename,
        region=None,
        genome=default_genome,
        annotator=annotation_pipeline_internal)
    denovo.load_simple_families()

    return denovo


@pytest.fixture
def vcf_import_config():
    fullpath = relative_to_this_test_folder(
        "fixtures/vcf_import/effects_trio"
    )
    config = Configure.from_prefix_vcf(fullpath)
    return config.vcf


@pytest.fixture
def vcf_import_raw(
        vcf_import_config, default_genome, annotation_pipeline_internal):
    freq_annotator = VcfAlleleFrequencyAnnotator()

    fvars = RawFamilyVariants(
        prefix=vcf_import_config.prefix,
        annotator=freq_annotator)
    fvars.annot_df = annotation_pipeline_internal.annotate_df(fvars.annot_df)

    return fvars


@pytest.fixture
def fixture_select(
        vcf_import_raw,
        annotation_pipeline_config, annotation_pipeline_default_config):
    def build(fixture_name):
        if fixture_name == 'vcf_import_raw':
            return vcf_import_raw
        elif fixture_name == 'annotation_pipeline_config':
            return annotation_pipeline_config
        elif fixture_name == 'annotation_pipeline_default_config':
            return annotation_pipeline_default_config
        else:
            raise ValueError(fixture_name)
    return build


@pytest.fixture(scope='session')
def dae_iossifov2014_config():
    fullpath = relative_to_this_test_folder(
        "fixtures/dae_iossifov2014/iossifov2014"
    )
    config = Configure.from_prefix_denovo(fullpath)
    return config.denovo


@pytest.fixture
def dae_iossifov2014(
        dae_iossifov2014_config, default_genome, annotation_pipeline_internal):
    config = dae_iossifov2014_config
    denovo = RawDenovo(
        config.denovo_filename,
        config.family_filename,
        genome=default_genome,
        annotator=annotation_pipeline_internal)
    denovo.load_simple_families()

    return denovo


@pytest.fixture(scope='session')
def variants_vcf(default_genome, default_gene_models):
    def builder(path):
        from dae.backends.vcf.builder import variants_builder

        a_path = os.path.join(
            relative_to_this_test_folder('fixtures'), path)
        fvars = variants_builder(
            a_path, genome=default_genome, gene_models=default_gene_models,
            force_reannotate=True)
        return fvars
    return builder


@pytest.fixture
def variants_implementations(
        variants_vcf, variants_impala):
    impls = {
        "variants_vcf": variants_vcf,
        "variants_impala": variants_impala,
    }
    return impls


@pytest.fixture
def variants_impl(variants_implementations):
    return lambda impl_name: variants_implementations[impl_name]


@pytest.fixture(scope='session')
def config_dae():
    def builder(path):
        fullpath = relative_to_this_test_folder(
            os.path.join("fixtures", path))
        config = Configure.from_prefix_dae(fullpath)
        return config
    return builder


@pytest.fixture(scope='session')
def raw_dae(config_dae, default_genome):
    def builder(path, region=None):
        config = config_dae(path)
        dae = RawDAE(
            config.dae.summary_filename,
            config.dae.toomany_filename,
            config.dae.family_filename,
            region=region,
            genome=default_genome,
            annotator=None)
        return dae
    return builder


@pytest.fixture(scope='session')
def config_denovo():
    def builder(path):
        fullpath = relative_to_this_test_folder(
            os.path.join("fixtures", path))
        config = Configure.from_prefix_denovo(fullpath)
        return config
    return builder


@pytest.fixture(scope='session')
def raw_denovo(config_denovo, default_genome):
    def builder(path):
        config = config_denovo(path)
        denovo = RawDenovo(
            config.denovo.denovo_filename,
            config.denovo.family_filename,
            genome=default_genome,
            annotator=None)
        return denovo
    return builder


def impala_test_dbname():
    return 'impala_test_db'


def pytest_addoption(parser):
    parser.addoption(
        "--reimport", action="store_true", default=False,
        help="force reimport"
    )


@pytest.fixture(scope='session')
def reimport(request):
    return bool(request.config.getoption("--reimport"))


# Impala backend
@pytest.fixture(scope='session')
def test_hdfs(request):
    from dae.backends.impala.hdfs_helpers import HdfsHelpers
    hdfs = HdfsHelpers.get_hdfs()
    return hdfs


@pytest.fixture(scope='session')
def test_impala_helpers(request):
    from dae.backends.impala.impala_helpers import ImpalaHelpers
    helpers = ImpalaHelpers()

    return helpers


def collect_vcf(dirname):
    result = []
    pattern = os.path.join(dirname, "*.vcf")
    for filename in glob.glob(pattern):
        prefix = os.path.splitext(filename)[0]
        vcf_config = Configure.from_prefix_vcf(prefix).vcf
        result.append(vcf_config)
    return result


def build_impala_config(vcf_config):
    study_id = os.path.basename(
        os.path.splitext(vcf_config.pedigree)[0])

    conf = {
        'impala': {
            'db': impala_test_dbname(),
            'tables': {
                'variant': '{}_variant'.format(study_id),
                'pedigree': '{}_pedigree'.format(study_id),
            }
        }
    }
    return Configure(conf).impala


DATA_IMPORT_COUNT = 0


@pytest.fixture(scope='session')
def data_import(
        request, test_hdfs, test_impala_helpers, reimport):

    global DATA_IMPORT_COUNT
    DATA_IMPORT_COUNT += 1

    assert DATA_IMPORT_COUNT == 1

    temp_dirname = test_hdfs.tempdir(prefix='variants_', suffix='_data')
    test_hdfs.mkdir(temp_dirname)

    dae_config = DAEConfig.read_and_parse_file_configuration()
    annotation_pipeline = construct_import_annotation_pipeline(
        dae_config)

    def fin():
        test_hdfs.delete(temp_dirname, recursive=True)
    request.addfinalizer(fin)

    def build(dirname):

        if not test_impala_helpers.check_database(impala_test_dbname()):
            test_impala_helpers.create_database(impala_test_dbname())

        vcfdirname = relative_to_this_test_folder(
            os.path.join("fixtures", dirname))
        vcf_configs = collect_vcf(vcfdirname)

        for vcf in vcf_configs:
            print("importing vcf:", vcf.vcf)
            impala = build_impala_config(vcf)
            if not reimport and \
                    test_impala_helpers.check_table(
                        impala_test_dbname(), impala.tables.variant) and \
                    test_impala_helpers.check_table(
                        impala_test_dbname(), impala.tables.pedigree):
                continue
            impala_config = import_vcf(
                dae_config, annotation_pipeline,
                vcf.pedigree, vcf.vcf,
                region=None, bucket_index=0,
                output=temp_dirname,
                filesystem=test_hdfs.filesystem())
            impala_config['db'] = impala_test_dbname()
            test_impala_helpers.import_variants(impala_config)

    build("backends/")
    return True


@pytest.fixture(scope='session')
def variants_impala(request, data_import, test_impala_helpers):

    def builder(path):
        from dae.backends.impala.impala_variants import ImpalaFamilyVariants

        vcf_prefix = relative_to_this_test_folder(
            os.path.join("fixtures", path))
        vcf_config = Configure.from_prefix_vcf(vcf_prefix).vcf
        impala_config = build_impala_config(vcf_config)
        fvars = ImpalaFamilyVariants(
            impala_config, test_impala_helpers.connection)
        return fvars
    return builder
