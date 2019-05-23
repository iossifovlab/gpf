
from builtins import str

import os
import pytest
import shutil
import tempfile
import time

import pandas as pd
from io import StringIO

from box import Box

from configurable_entities.configuration import DAEConfig

from annotation.annotation_pipeline import PipelineAnnotator

from backends.configure import Configure
from backends.thrift.raw_dae import RawDAE, RawDenovo
from backends.thrift.import_tools import variants_iterator_to_parquet
from backends.thrift.raw_thrift import ThriftFamilyVariants
from backends.vcf.raw_vcf import RawFamilyVariants
from backends.vcf.annotate_allele_frequencies import \
    VcfAlleleFrequencyAnnotator


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
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


@pytest.fixture(scope='session')
def annotation_pipeline_config():
    filename = relative_to_this_test_folder(
        "tests/fixtures/annotation_pipeline/import_annotation.conf")
    return filename


@pytest.fixture(scope='session')
def annotation_pipeline_default_config():
    dae_config = DAEConfig()
    return dae_config.annotation_conf


@pytest.fixture(scope='session')
def annotation_scores_dirname():
    filename = relative_to_this_test_folder(
        "tests/fixtures/annotation_pipeline/")
    return filename


@pytest.fixture(scope='session')
def annotation_pipeline_vcf():
    filename = relative_to_this_test_folder(
        "tests/fixtures/annotation_pipeline/import_annotation.conf")

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
                "tests/fixtures/annotation_pipeline/")
        })
    return pipeline


@pytest.fixture(scope='session')
def annotation_pipeline_internal():
    filename = relative_to_this_test_folder(
        "tests/fixtures/annotation_pipeline/import_annotation.conf")

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
                "tests/fixtures/annotation_pipeline/")
        })
    return pipeline


@pytest.fixture(scope='session')
def default_genome():
    from DAE import genomesDB
    genome = genomesDB.get_genome()  # @UndefinedVariable
    return genome


@pytest.fixture(scope='session')
def default_gene_models():
    from DAE import genomesDB
    gene_models = genomesDB.get_gene_models("RefSeq2013")
    return gene_models


@pytest.fixture
def dae_denovo_config():
    fullpath = relative_to_this_test_folder(
        "tests/fixtures/dae_denovo/denovo"
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
        "tests/fixtures/dae_transmitted/transmission"
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
        "tests/fixtures/vcf_import/effects_trio"
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
def vcf_import_thrift(
        vcf_import_raw, annotation_pipeline_internal, temp_dirname):
    variants_iterator_to_parquet(
        vcf_import_raw,
        temp_dirname,
        annotation_pipeline=annotation_pipeline_internal
    )
    fvars = ThriftFamilyVariants(prefix=temp_dirname)
    return fvars


@pytest.fixture
def fixture_select(
        vcf_import_raw, vcf_import_thrift,
        annotation_pipeline_config, annotation_pipeline_default_config):
    def build(fixture_name):
        if fixture_name == 'vcf_import_thift':
            return vcf_import_thrift
        elif fixture_name == 'vcf_import_raw':
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
        "tests/fixtures/dae_iossifov2014/iossifov2014"
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
def parquet_thrift(testing_thriftserver):
    def builder(parquet_config):
        return ThriftFamilyVariants(
            config=parquet_config,
            thrift_connection=testing_thriftserver)
    return builder


@pytest.fixture(scope='session')
def testing_thriftserver(request):
    from impala.dbapi import connect

    spark_home = os.environ.get("SPARK_HOME")
    assert spark_home is not None

    thrift_host = os.getenv("THRIFTSERVER_HOST", "127.0.0.1")
    thrift_port = int(os.getenv("THRIFTSERVER_PORT", 10000))

    def thrift_connect(retries=200):
        for count in range(retries + 1):
            try:
                time.sleep(2.0)
                print("trying to connect to thrift server: try={}".format(
                    count + 1))
                conn = connect(host=thrift_host, port=thrift_port,
                               auth_mechanism='PLAIN')
                return conn
            except Exception as ex:
                print("connect to thriftserver failed:", ex)
        return None

    conn = thrift_connect(3)
    if conn is not None:
        return conn

    start_cmd = "{}/sbin/start-thriftserver.sh " \
        "--hiveconf hive.server2.thrift.port={}".format(
            spark_home, thrift_port)

    print("starting thrift command: ", start_cmd)
    os.system(start_cmd)

    return thrift_connect()
