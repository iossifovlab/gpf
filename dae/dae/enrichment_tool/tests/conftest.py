# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import cast, Generator

import pytest

from box import Box

from dae.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from dae.genomic_resources.testing import \
    convert_to_tab_separated, build_inmemory_test_repository
from dae.genomic_resources.repository import GR_CONF_FILE_NAME, \
    GenomicResourceRepo
from dae.genomic_resources.group_repository import GenomicResourceGroupRepo


from dae.enrichment_tool.gene_weights_background import \
    GeneWeightsEnrichmentBackground
from dae.enrichment_tool.samocha_background import \
    SamochaEnrichmentBackground


@pytest.fixture(scope="session")
def gpf_fixture(
    fixtures_gpf_instance: GPFInstance,
    grr: GenomicResourceRepo,
) -> Generator[GPFInstance, None, None]:
    original_grr = fixtures_gpf_instance.grr
    fixtures_gpf_instance.grr = GenomicResourceGroupRepo(
        [grr, original_grr], "enrichment_testing_repo"
    )

    yield fixtures_gpf_instance

    fixtures_gpf_instance.grr = original_grr


@pytest.fixture(scope="session")
def f1_trio_enrichment_config(gpf_fixture: GPFInstance) -> Box:
    config = gpf_fixture.get_genotype_data_config("f1_trio")
    assert config is not None

    return cast(Box, config["enrichment"])


@pytest.fixture(scope="session")
def f1_trio(gpf_fixture: GPFInstance) -> GenotypeData:
    result = gpf_fixture.get_genotype_data("f1_trio")
    return result


@pytest.fixture(scope="session")
def coding_len_background(
    grr: GenomicResourceRepo
) -> GeneWeightsEnrichmentBackground:
    res = grr.get_resource("enrichment/coding_len_testing")
    assert res.get_type() == "gene_weights_enrichment_background"

    background = GeneWeightsEnrichmentBackground(res)
    assert background is not None
    assert background.name == "CodingLenBackground"

    background.load()
    return background


@pytest.fixture(scope="session")
def samocha_background(
    grr: GenomicResourceRepo
) -> SamochaEnrichmentBackground:
    res = grr.get_resource("enrichment/samocha_testing")
    assert res.get_type() == "samocha_enrichment_background"

    background = SamochaEnrichmentBackground(res)
    assert background is not None
    assert background.name == "Samocha's enrichment background model"
    assert background.background_type == "samocha_enrichment_background"

    background.load()
    return background


@pytest.fixture(scope="session")
def grr() -> GenomicResourceRepo:
    return build_inmemory_test_repository({
        "enrichment": {
            "coding_len_testing": {
                GR_CONF_FILE_NAME: """
                    type: gene_weights_enrichment_background
                    filename: data.mem
                    name: CodingLenBackground
                """,
                "data.mem": convert_to_tab_separated("""
                    gene     gene_weight
                    SAMD11   3
                    PLEKHN1  7
                    POGZ     13
                """)
            },
            "samocha_testing": {
                GR_CONF_FILE_NAME: """
                    type: samocha_enrichment_background
                    filename: data.mem
                """,
                "data.mem": convert_to_tab_separated("""
"transcript","gene","bp","all","synonymous","missense","nonsense","splice-site","frame-shift","F","M","P_LGDS","P_MISSENSE","P_SYNONYMOUS"
"NM_017582","SAMD11",3,-1,-5,-4,-6,-6,-6,2,2,1.1,1.4,5.7
"NM_017582","PLEKHN1",7,-2,-5,-4,-6,-6,-6,2,2,1.2,1.5,5.8
"NM_014372","POGZ",11,-3,-5,-5,-6,-7,-6,2,2,6.3,4.6,2.9
                """)
            }
        }
    })
