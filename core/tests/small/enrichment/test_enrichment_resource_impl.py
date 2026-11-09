# pylint: disable=W0621,C0114,C0116
import pytest
from gain.genomic_resources.repository import GR_CONF_FILE_NAME
from gain.genomic_resources.testing import (
    build_inmemory_test_resource,
    convert_to_tab_separated,
)

from gpf.enrichment_tool.resource_implementations.enrichment_resource_impl import (  # ruff: ignore[line-too-long]
    EnrichmentBackgroundResourceImplementation,
    build_gene_weights_enrichment_background,
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
    return build_gene_weights_enrichment_background(res)


def test_create_statistics_build_tasks_rejects_unknown_keyword(
    impl: EnrichmentBackgroundResourceImplementation,
) -> None:
    with pytest.raises(TypeError, match="region_sise"):
        impl.create_statistics_build_tasks(region_sise=10)  # type: ignore[call-arg]


def test_create_statistics_build_tasks_accepts_base_keywords(
    impl: EnrichmentBackgroundResourceImplementation,
) -> None:
    tasks = impl.create_statistics_build_tasks(region_size=10, grr=None)

    assert tasks == []
