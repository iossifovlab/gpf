# pylint: disable=W0621,C0114,C0116
from typing import Any

import pytest
from gain.genomic_resources.repository import GR_CONF_FILE_NAME
from gain.genomic_resources.testing import (
    build_inmemory_test_resource,
    convert_to_tab_separated,
)

from gpf.enrichment_tool.resource_implementations import (
    enrichment_resource_impl,
)

EnrichmentBackgroundResourceImplementation = (
    enrichment_resource_impl.EnrichmentBackgroundResourceImplementation
)


@pytest.fixture
def impl() -> EnrichmentBackgroundResourceImplementation:
    res = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: gene_weights_enrichment_background
            filename: data.mem
            name: TestingGeneWeightsBackground
        """,
        "data.mem": convert_to_tab_separated("""
            gene   gene_weight
            A      10
            B      20
        """),
    })
    return enrichment_resource_impl.build_gene_weights_enrichment_background(
        res)


def test_create_statistics_build_tasks_rejects_unknown_keyword(
    impl: EnrichmentBackgroundResourceImplementation,
) -> None:
    misspelled: dict[str, Any] = {"region_sise": 10}

    with pytest.raises(TypeError, match="region_sise"):
        impl.create_statistics_build_tasks(**misspelled)


def test_create_statistics_build_tasks_accepts_base_keywords(
    impl: EnrichmentBackgroundResourceImplementation,
) -> None:
    tasks = impl.create_statistics_build_tasks(region_size=10, grr=None)

    assert tasks == []
