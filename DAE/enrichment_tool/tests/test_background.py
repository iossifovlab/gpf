# from enrichment_tool.background import BackgroundBase, SynonymousBackground,\
#     CodingLenBackground, SamochaBackground
from enrichment_tool.background import BackgroundBase, CodingLenBackground, \
    SamochaBackground


def test_background_base_backgrounds():
    backgrounds = BackgroundBase.backgrounds()

    # assert len(backgrounds) == 3
    assert len(backgrounds) == 2
    # assert backgrounds['synonymousBackgroundModel'] == SynonymousBackground
    assert backgrounds['codingLenBackgroundModel'] == CodingLenBackground
    assert backgrounds['samochaBackgroundModel'] == SamochaBackground
