# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.effect_annotation.effect import AlleleEffects, EffectTranscript


EFFECT_DATA_1 = "splice-site!" \
    "NUDT4:splice-site|" \
    "NUDT4B:splice-site|" \
    "NUDT4:splice-site|" \
    "NUDT4P2:non-coding-intron!" \
    "NM_001301022:NUDT4:splice-site:63/129|" \
    "NM_001301023:NUDT4:splice-site:62/128|" \
    "NM_001301024:NUDT4:splice-site:62/128|" \
    "NM_001355407:NUDT4B:splice-site:115/181|" \
    "NM_019094:NUDT4:splice-site:114/180|" \
    "NM_199040:NUDT4:splice-site:115/181|" \
    "NR_104005:NUDT4P2:non-coding-intron:None/None[None]"


EFFECT_TRANSCRIPT_DATA_1 = "NM_031857:PCDHA9:3'UTR:1480"


def test_effect_transcript_deserialization() -> None:
    effect_trancript = EffectTranscript.from_string(EFFECT_TRANSCRIPT_DATA_1)
    assert str(effect_trancript) == EFFECT_TRANSCRIPT_DATA_1


def test_allele_effect_deserialization() -> None:
    allele_effect = AlleleEffects.from_string(EFFECT_DATA_1)

    assert str(allele_effect) == EFFECT_DATA_1
