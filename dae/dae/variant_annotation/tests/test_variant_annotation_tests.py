from dae.variant_annotation.annotator import VariantAnnotator


def test_synonymous_complex_var(genomic_sequence_2013, gene_models_2013):
    [effect] = VariantAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="1:897349",
        var="complex(GG->AA)",
    )

    assert effect.gene == "KLHL17"
    assert effect.transcript_id == "NM_198317_1"
    assert effect.strand == "+"
    assert effect.effect == "missense"
    assert effect.prot_pos == 211
    assert effect.prot_length == 642
    assert effect.aa_change == "Lys,Ala->Lys,Thr"


def test_just_next_to_splice_site_var(genomic_sequence_2013, gene_models_2013):
    effects = VariantAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="5:86705101", var="del(4)"
    )

    assert len(effects) == 2
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "CCNH"
    assert effects_sorted[0].transcript_id == "NM_001199189_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "intron"
    # assert effects_sorted[0].prot_pos is None
    # assert effects_sorted[0].prot_length is None
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "CCNH"
    assert effects_sorted[1].transcript_id == "NM_001239_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "intron"
    # assert effects_sorted[1].prot_pos is None
    # assert effects_sorted[1].prot_length is None
    assert effects_sorted[1].aa_change is None


def test_chr2_32853362_ins_var(genomic_sequence_2013, gene_models_2013):
    effects = VariantAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="6:157527729",
        var="complex(CTGG->ATAG)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "ARID1B"
    assert effects_sorted[0].transcript_id == "NM_017519_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "nonsense"
    # assert effects_sorted[0].prot_pos is None
    # assert effects_sorted[0].prot_length is None
    assert effects_sorted[0].aa_change == "His,Trp->Gln,End"

    assert effects_sorted[1].gene == "ARID1B"
    assert effects_sorted[1].transcript_id == "NM_020732_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "nonsense"
    assert effects_sorted[1].prot_pos, 1
    assert effects_sorted[1].prot_length, 843
    assert effects_sorted[1].aa_change == "His,Trp->Gln,End"


def test_chr5_75902128_sub_var(genomic_sequence_2013, gene_models_2013):
    [effect] = VariantAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="5:75902128",
        var="sub(C->T)",
    )

    assert effect.gene == "IQGAP2"
    assert effect.transcript_id == "NM_006633_1"
    assert effect.strand == "+"
    assert effect.effect == "nonsense"
    # assert effect.prot_pos is None
    # assert effect.prot_length is None
    assert effect.aa_change == "Arg->End"
