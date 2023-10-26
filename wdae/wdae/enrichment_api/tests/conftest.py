# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from enrichment_api.enrichment_builder import EnrichmentBuilder
from enrichment_api.enrichment_serializer import EnrichmentSerializer

from dae.enrichment_tool.event_counters import EventsCounter
from dae.enrichment_tool.tool import EnrichmentTool
from dae.enrichment_tool.background_facade import BackgroundFacade
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData


@pytest.fixture(scope="session")
def background_facade(fixtures_wgpf_instance: GPFInstance) -> BackgroundFacade:
    return fixtures_wgpf_instance._background_facade


@pytest.fixture(scope="session")
def f1_trio(fixtures_wgpf_instance: GPFInstance) -> GenotypeData:
    return fixtures_wgpf_instance.get_genotype_data("f1_trio")


@pytest.fixture(scope="session")
def enrichment_builder(
    f1_trio: GenotypeData, background_facade: BackgroundFacade
) -> EnrichmentBuilder:
    enrichment_config = background_facade.get_study_enrichment_config(
        f1_trio
    )
    backgorund = background_facade.get_study_background(
        f1_trio, "enrichment/coding_len_testing"
    )
    assert backgorund is not None

    counter = EventsCounter()
    enrichment_tool = EnrichmentTool(
        enrichment_config, backgorund, counter)
    builder = EnrichmentBuilder(
        f1_trio, enrichment_tool, ["SAMD11", "PLEKHN1", "POGZ"]
    )

    return builder


@pytest.fixture(scope="session")
def enrichment_serializer(
    background_facade: BackgroundFacade,
    enrichment_builder: EnrichmentBuilder,
    f1_trio: GenotypeData
) -> EnrichmentSerializer:
    enrichment_config = background_facade.get_study_enrichment_config(
        f1_trio
    )
    build = enrichment_builder._build_results()
    serializer = EnrichmentSerializer(enrichment_config, build)

    return serializer
