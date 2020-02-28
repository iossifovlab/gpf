# from enrichment_tool.background import BackgroundBase, SynonymousBackground,\
#     CodingLenBackground, SamochaBackground
from dae.enrichment_tool.background import (
    BackgroundBase,
    CodingLenBackground,
    SamochaBackground,
)


def test_background_base_backgrounds():
    backgrounds = BackgroundBase.backgrounds()

    # assert len(backgrounds) == 3
    assert len(backgrounds) == 2
    # assert backgrounds['synonymous_background_model'] == SynonymousBackground
    assert backgrounds["coding_len_background_model"] == CodingLenBackground
    assert backgrounds["samocha_background_model"] == SamochaBackground
