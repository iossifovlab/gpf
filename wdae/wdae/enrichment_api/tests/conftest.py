# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from enrichment_api.enrichment_builder import EnrichmentBuilder
from enrichment_api.enrichment_serializer import EnrichmentSerializer

from dae.enrichment_tool.enrichment_helper import EnrichmentHelper
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData


@pytest.fixture(scope="session")
def enrichment_helper(fixtures_wgpf_instance: GPFInstance) -> EnrichmentHelper:
    return EnrichmentHelper(fixtures_wgpf_instance.grr)


@pytest.fixture(scope="session")
def f1_trio(fixtures_wgpf_instance: GPFInstance) -> GenotypeData:
    return fixtures_wgpf_instance.get_genotype_data("f1_trio")


@pytest.fixture(scope="session")
def enrichment_builder(
    f1_trio: GenotypeData,
    enrichment_helper: EnrichmentHelper
) -> EnrichmentBuilder:

    builder = EnrichmentBuilder(
        enrichment_helper,
        f1_trio,
        ["SAMD11", "PLEKHN1", "POGZ"],
        "enrichment/coding_len_testing",
        "enrichment_events_counting"
    )

    return builder


@pytest.fixture(scope="session")
def enrichment_serializer(
    enrichment_helper: EnrichmentHelper,
    enrichment_builder: EnrichmentBuilder,
    f1_trio: GenotypeData
) -> EnrichmentSerializer:
    enrichment_config = enrichment_helper.get_enrichment_config(f1_trio)
    assert enrichment_config is not None

    build = enrichment_builder.build_results()
    serializer = EnrichmentSerializer(enrichment_config, build)

    return serializer
