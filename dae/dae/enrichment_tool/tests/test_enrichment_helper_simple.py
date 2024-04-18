# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.enrichment_tool.enrichment_helper import EnrichmentHelper
from dae.enrichment_tool.gene_weights_background import (
    GeneScoreEnrichmentBackground,
)
from dae.enrichment_tool.samocha_background import SamochaEnrichmentBackground
from dae.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData


def test_gpf_fixture(gpf_fixture: GPFInstance) -> None:
    grr = gpf_fixture.grr
    res = grr.get_resource("enrichment/samocha_testing")
    assert res.get_type() == "samocha_enrichment_background"


def test_get_study_background(
    f1_trio: GenotypeData,
    gpf_fixture: GPFInstance,
) -> None:
    assert gpf_fixture.grr.repo_id == "enrichment_testing_repo"

    helper = EnrichmentHelper(gpf_fixture.grr)

    assert isinstance(
        helper.create_background(
            "enrichment/coding_len_testing",
        ),
        GeneScoreEnrichmentBackground,
    )

    assert isinstance(
        helper.create_background(
            "enrichment/samocha_testing",
        ),
        SamochaEnrichmentBackground,
    )


def test_get_study_enrichment_config(
    f1_trio: GenotypeData,
    gpf_fixture: GPFInstance,
) -> None:
    helper = EnrichmentHelper(gpf_fixture.grr)
    assert helper.get_enrichment_config(f1_trio) is not None


def test_has_enrichment_config(
    f1_trio: GenotypeData,
    gpf_fixture: GPFInstance,
) -> None:

    helper = EnrichmentHelper(gpf_fixture.grr)
    assert helper.has_enrichment_config(f1_trio) is True
