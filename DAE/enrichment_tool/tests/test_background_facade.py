# from enrichment_tool.background import SynonymousBackground, \
#     CodingLenBackground, SamochaBackground
from enrichment_tool.background import CodingLenBackground, SamochaBackground


def test_get_study_background(background_facade):
    # assert isinstance(background_facade.get_study_background(
    #     'f1_trio', 'synonymousBackgroundModel'), SynonymousBackground)

    assert isinstance(background_facade.get_study_background(
        'f1_trio', 'codingLenBackgroundModel'), CodingLenBackground)

    assert isinstance(background_facade.get_study_background(
        'f1_trio', 'samochaBackgroundModel'), SamochaBackground)

    assert background_facade.get_study_background('f1_trio', 'Model') is None
    assert background_facade.get_study_background('f1', 'Model') is None


def test_get_all_study_backgrounds(background_facade):
    backgrounds = background_facade.get_all_study_backgrounds('f1_trio')

    # assert len(backgrounds) == 3
    assert len(backgrounds) == 2
    # assert isinstance(
    #     backgrounds['synonymousBackgroundModel'], SynonymousBackground)
    assert isinstance(
        backgrounds['codingLenBackgroundModel'], CodingLenBackground)
    assert isinstance(
        backgrounds['samochaBackgroundModel'], SamochaBackground)

    assert background_facade.get_all_study_backgrounds('f1') is None


def test_get_study_enrichment_config(background_facade):
    assert background_facade.get_study_enrichment_config('f1_trio') is not None
    assert background_facade.get_study_enrichment_config('f1') is None


def test_get_all_study_ids(background_facade):
    assert background_facade.get_all_study_ids() == ['f1_trio']


def test_has_background(background_facade):
    # assert background_facade.has_background(
    #     'f1_trio', 'synonymousBackgroundModel') is True

    assert background_facade.has_background(
        'f1_trio', 'codingLenBackgroundModel') is True

    assert background_facade.has_background(
        'f1_trio', 'samochaBackgroundModel') is True

    assert background_facade.has_background('f1_trio', 'Model') is False
    assert background_facade.has_background('f1', 'Model') is False
