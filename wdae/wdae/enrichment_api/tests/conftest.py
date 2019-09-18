import os
import pytest

from dae.gpf_instance.gpf_instance import GPFInstance

from datasets_api.studies_manager import StudiesManager

from enrichment_api.enrichment_builder import EnrichmentBuilder
from enrichment_api.enrichment_serializer import EnrichmentSerializer

from dae.enrichment_tool.event_counters import EventsCounter
from dae.enrichment_tool.tool import EnrichmentTool


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='function')
def gpf_instance():
    return GPFInstance(work_dir=fixtures_dir())


@pytest.fixture(scope='function')
def variants_db_fixture(gpf_instance):
    return gpf_instance.variants_db


@pytest.fixture(scope='function')
def studies_manager(db, gpf_instance):
    return StudiesManager(gpf_instance)


@pytest.fixture(scope='function')
def mock_studies_manager(mocker, studies_manager):
    mocker.patch(
        'enrichment_api.views.get_studies_manager',
        return_value=studies_manager)
    mocker.patch(
        'gene_sets.expand_gene_set_decorator.get_studies_manager',
        return_value=studies_manager)
    mocker.patch(
        'datasets_api.permissions.get_studies_manager',
        return_value=studies_manager)


@pytest.fixture(scope='function')
def background_facade(studies_manager):
    return studies_manager.get_background_facade()


@pytest.fixture(scope='function')
def f1_trio(variants_db_fixture):
    f1_trio = variants_db_fixture.get('f1_trio')
    return f1_trio


@pytest.fixture(scope='function')
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


@pytest.fixture(scope='function')
def enrichment_serializer(background_facade, enrichment_builder):
    enrichment_config = \
        background_facade.get_study_enrichment_config('f1_trio')
    build = enrichment_builder.build()
    serializer = EnrichmentSerializer(enrichment_config, build)

    return serializer
