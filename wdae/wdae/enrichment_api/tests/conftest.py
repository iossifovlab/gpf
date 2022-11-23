# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from enrichment_api.enrichment_builder import EnrichmentBuilder
from enrichment_api.enrichment_serializer import EnrichmentSerializer

from dae.enrichment_tool.event_counters import EventsCounter
from dae.enrichment_tool.tool import EnrichmentTool


@pytest.fixture(scope="session")
def background_facade(fixtures_gpf_instance):
    return fixtures_gpf_instance._background_facade


@pytest.fixture(scope="session")
def f1_trio(fixtures_gpf_instance):
    variants_db = fixtures_gpf_instance._variants_db
    f1_trio = variants_db.get("f1_trio")
    return f1_trio


@pytest.fixture(scope="session")
def enrichment_builder(f1_trio, background_facade):
    enrichment_config = background_facade.get_study_enrichment_config(
        "f1_trio"
    )
    backgorund = background_facade.get_study_background(
        "f1_trio", "coding_len_background_model"
    )
    counter = EventsCounter()
    enrichment_tool = EnrichmentTool(enrichment_config, backgorund, counter)
    builder = EnrichmentBuilder(
        f1_trio, enrichment_tool, ["SAMD11", "PLEKHN1", "POGZ"]
    )

    return builder


@pytest.fixture(scope="session")
def enrichment_serializer(background_facade, enrichment_builder):
    enrichment_config = background_facade.get_study_enrichment_config(
        "f1_trio"
    )
    build = enrichment_builder._build_results()
    serializer = EnrichmentSerializer(enrichment_config, build)

    return serializer
