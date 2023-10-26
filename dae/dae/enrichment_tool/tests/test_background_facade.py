# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.studies.study import GenotypeData
from dae.enrichment_tool.gene_weights_background import \
    GeneWeightsEnrichmentBackground
from dae.enrichment_tool.samocha_background import \
    SamochaEnrichmentBackground
from dae.enrichment_tool.background_facade import BackgroundFacade
from dae.gpf_instance import GPFInstance


def test_gpf_fixture(gpf_fixture: GPFInstance) -> None:
    grr = gpf_fixture.grr
    res = grr.get_resource("enrichment/samocha_testing")
    assert res.get_type() == "samocha_enrichment_background"


def test_get_study_background(
    f1_trio: GenotypeData,
    background_facade: BackgroundFacade
) -> None:
    assert background_facade.grr.repo_id == "enrichment_testing_repo"

    assert isinstance(
        background_facade.get_study_background(
            f1_trio, "enrichment/coding_len_testing"
        ),
        GeneWeightsEnrichmentBackground,
    )

    assert isinstance(
        background_facade.get_study_background(
            f1_trio, "enrichment/samocha_testing"
        ),
        SamochaEnrichmentBackground,
    )

    assert background_facade.get_study_background(f1_trio, "Model") is None
    # assert background_facade.get_study_background("f1", "Model") is None


# def test_get_all_study_backgrounds(
#         background_facade: BackgroundFacade) -> None:
#     backgrounds = background_facade.get_all_study_backgrounds("f1_trio")

#     assert backgrounds is not None
#     assert len(backgrounds) == 2
#     # assert isinstance(
#     #     backgrounds['synonymous_background_model'], SynonymousBackground)
#     assert isinstance(
#         backgrounds["coding_len_background_model"], CodingLenBackground
#     )
#     assert isinstance(
#         backgrounds["samocha_background_model"], SamochaBackground
#     )

#     assert background_facade.get_all_study_backgrounds("f1") is None


def test_get_study_enrichment_config(
    f1_trio: GenotypeData,
    background_facade: BackgroundFacade
) -> None:
    assert background_facade.get_study_enrichment_config(f1_trio) is not None


def test_has_background(
    f1_trio: GenotypeData,
    background_facade: BackgroundFacade
) -> None:
    # assert background_facade.has_background(
    #     'f1_trio', 'synonymous_background_model') is True

    assert (
        background_facade.has_background(
            f1_trio, "enrichment/coding_len_testing"
        )
        is True
    )

    assert (
        background_facade.has_background(
            f1_trio, "enrichment/samocha_testing")
        is True
    )

    assert background_facade.has_background(f1_trio, "Model") is False
