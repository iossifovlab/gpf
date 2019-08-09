import os
import pytest

from dae.configuration.configuration import DAEConfig
from dae.studies.factory import VariantsDb

from datasets_api.studies_manager import StudiesManager

from enrichment_api.enrichment_builder import EnrichmentBuilder
from enrichment_api.enrichment_serializer import EnrichmentSerializer

from dae.enrichment_tool.event_counters import EventsCounter
from dae.enrichment_tool.tool import EnrichmentTool


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture()
def dae_config_fixture():
    dae_config = DAEConfig.make_config(fixtures_dir())
    return dae_config


@pytest.fixture()
def variants_db_fixture(dae_config_fixture):
    variants_db = VariantsDb(dae_config_fixture)
    return variants_db


@pytest.fixture()
def studies_manager(dae_config_fixture):
    return StudiesManager(dae_config_fixture)


@pytest.fixture()
def mock_studies_manager(db, mocker, studies_manager):
    studies_manager.reload_dataset()
    mocker.patch(
        'enrichment_api.views.get_studies_manager',
        return_value=studies_manager)
    mocker.patch(
        'gene_sets.expand_gene_set_decorator.get_studies_manager',
        return_value=studies_manager)
    mocker.patch(
        'datasets_api.permissions.get_studies_manager',
        return_value=studies_manager)


@pytest.fixture()
def background_facade(studies_manager):
    return studies_manager.get_background_facade()


@pytest.fixture()
def f1_trio(variants_db_fixture):
    f1_trio = variants_db_fixture.get('f1_trio')
    return f1_trio


@pytest.fixture()
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


@pytest.fixture()
def enrichment_serializer(background_facade, enrichment_builder):
    enrichment_config = \
        background_facade.get_study_enrichment_config('f1_trio')
    build = enrichment_builder.build()
    serializer = EnrichmentSerializer(enrichment_config, build)

    return serializer
