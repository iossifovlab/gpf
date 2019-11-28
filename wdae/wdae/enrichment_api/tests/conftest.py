import os
import pytest

from dae.gpf_instance.gpf_instance import GPFInstance
from gpf_instance.gpf_instance import reload_datasets

from enrichment_api.enrichment_builder import EnrichmentBuilder
from enrichment_api.enrichment_serializer import EnrichmentSerializer

from dae.enrichment_tool.event_counters import EventsCounter
from dae.enrichment_tool.tool import EnrichmentTool


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='session')
def gpf_instance(mock_genomes_db):
    return GPFInstance(work_dir=fixtures_dir())


@pytest.fixture(scope='session')
def variants_db_fixture(gpf_instance):
    return gpf_instance.variants_db


@pytest.fixture(scope='function')
def mock_gpf_instance(db, mocker, gpf_instance):
    reload_datasets(gpf_instance.variants_db)
    mocker.patch(
        'query_base.query_base.get_gpf_instance',
        return_value=gpf_instance
    )
    mocker.patch(
        'gene_sets.expand_gene_set_decorator.get_gpf_instance',
        return_value=gpf_instance
    )
    mocker.patch(
        'datasets_api.permissions.get_gpf_instance',
        return_value=gpf_instance
    )


@pytest.fixture(scope='session')
def background_facade(gpf_instance):
    return gpf_instance.background_facade


@pytest.fixture(scope='session')
def f1_trio(variants_db_fixture):
    f1_trio = variants_db_fixture.get('f1_trio')
    return f1_trio


@pytest.fixture(scope='session')
def enrichment_builder(f1_trio, background_facade):
    enrichment_config = \
        background_facade.get_study_enrichment_config('f1_trio')
    backgorund = background_facade.get_study_background(
        'f1_trio', 'codingLenBackgroundModel')
    counter = EventsCounter()
    enrichment_tool = EnrichmentTool(enrichment_config, backgorund, counter)
    builder = EnrichmentBuilder(
        f1_trio, enrichment_tool, ['SAMD11', 'PLEKHN1', 'POGZ'])

    return builder


@pytest.fixture(scope='session')
def enrichment_serializer(background_facade, enrichment_builder):
    enrichment_config = \
        background_facade.get_study_enrichment_config('f1_trio')
    build = enrichment_builder.build()
    serializer = EnrichmentSerializer(enrichment_config, build)

    return serializer
