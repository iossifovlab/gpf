# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.enrichment_tool.background import \
    CodingLenBackground, \
    SamochaBackground
from dae.enrichment_tool.background_facade import BackgroundFacade


def test_get_study_background(background_facade: BackgroundFacade) -> None:
    # assert isinstance(background_facade.get_study_background(
    #     'f1_trio', 'synonymous_background_model'), SynonymousBackground)

    assert isinstance(
        background_facade.get_study_background(
            "f1_trio", "coding_len_background_model"
        ),
        CodingLenBackground,
    )

    assert isinstance(
        background_facade.get_study_background(
            "f1_trio", "samocha_background_model"
        ),
        SamochaBackground,
    )

    assert background_facade.get_study_background("f1_trio", "Model") is None
    assert background_facade.get_study_background("f1", "Model") is None


def test_get_all_study_backgrounds(
        background_facade: BackgroundFacade) -> None:
    backgrounds = background_facade.get_all_study_backgrounds("f1_trio")

    assert backgrounds is not None
    assert len(backgrounds) == 2
    # assert isinstance(
    #     backgrounds['synonymous_background_model'], SynonymousBackground)
    assert isinstance(
        backgrounds["coding_len_background_model"], CodingLenBackground
    )
    assert isinstance(
        backgrounds["samocha_background_model"], SamochaBackground
    )

    assert background_facade.get_all_study_backgrounds("f1") is None


def test_get_study_enrichment_config(
        background_facade: BackgroundFacade) -> None:
    assert background_facade.get_study_enrichment_config("f1_trio") is not None
    assert background_facade.get_study_enrichment_config("f1") is None


def test_get_all_study_ids(background_facade: BackgroundFacade) -> None:
    print(background_facade.get_all_study_ids())
    assert background_facade.get_all_study_ids() == ["f1_trio"]


def test_has_background(background_facade: BackgroundFacade) -> None:
    # assert background_facade.has_background(
    #     'f1_trio', 'synonymous_background_model') is True

    assert (
        background_facade.has_background(
            "f1_trio", "coding_len_background_model"
        )
        is True
    )

    assert (
        background_facade.has_background("f1_trio", "samocha_background_model")
        is True
    )

    assert background_facade.has_background("f1_trio", "Model") is False
    assert background_facade.has_background("f1", "Model") is False
