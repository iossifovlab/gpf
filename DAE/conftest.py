import os
import pytest
import shutil
import tempfile

from box import Box

from annotation.annotation_pipeline import PipelineAnnotator
from backends.thrift.raw_dae import RawDAE, RawDenovo
from backends.configure import Configure


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


@pytest.fixture
def temp_dirname(request):
    dirname = tempfile.mkdtemp(suffix='_data', prefix='variants_')

    def fin():
        shutil.rmtree(dirname)

    request.addfinalizer(fin)
    return dirname


@pytest.fixture(scope='session')
def annotation_pipeline_configname():
    filename = relative_to_this_test_folder(
        "tests/fixtures/annotation_pipeline/import_annotation.conf")
    return filename


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
    gene_models = genomesDB.get_gene_models()  # @UndefinedVariable
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
