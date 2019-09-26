import pytest

from dae.variant_annotation.annotator import VariantAnnotator \
    as VariantAnnotation


def test_chr1_120387132_del_var(default_genome, default_gene_models):
    [effect] = VariantAnnotation.annotate_variant(
        default_gene_models, default_genome, loc='1:120387132', var='del(71)'
    )

    assert effect.gene == 'NBPF7'
    assert effect.transcript_id == 'NM_001047980_1'
    assert effect.strand == '-'
    assert effect.effect == 'noStart'
    assert effect.prot_pos == 1
    assert effect.prot_length == 421
    assert effect.aa_change is None


def test_chr2_237172988_ins_var(default_genome, default_gene_models):
    [effect] = VariantAnnotation.annotate_variant(
        default_gene_models, default_genome, loc='2:237172988',
        var='ins(TTGTTACG)'
    )

    assert effect.gene == 'ASB18'
    assert effect.transcript_id == 'NM_212556_1'
    assert effect.strand == '-'
    assert effect.effect == 'noStart'
    assert effect.prot_pos == 1
    assert effect.prot_length == 466
    assert effect.aa_change is None


@pytest.mark.skip()
def test_chr1_802610_867930_CNV_var(default_genome, default_gene_models):
    effects = VariantAnnotation.annotate_variant(
        default_gene_models, default_genome, loc='1:802610-867930', var='CNV+'
    )
    assert len(effects) == 3
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == 'SAMD11'
    assert effects_sorted[0].transcript_id == 'NM_152486_1'
    assert effects_sorted[0].strand == '+'
    assert effects_sorted[0].effect == 'unknown'
    # assert effects_sorted[0].prot_pos is None
    # assert effects_sorted[0].prot_length is None
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == 'LOC100130417'
    assert effects_sorted[1].transcript_id == 'NR_026874_1'
    assert effects_sorted[1].strand == '-'
    assert effects_sorted[1].effect == 'unknown'
    # assert effects_sorted[1].prot_pos is None
    # assert effects_sorted[1].prot_length is None
    assert effects_sorted[1].aa_change is None

    assert effects_sorted[2].gene == 'FAM41C'
    assert effects_sorted[2].transcript_id == 'NR_027055_1'
    assert effects_sorted[2].strand == '-'
    assert effects_sorted[2].effect == 'unknown'
    # assert effects_sorted[2].prot_pos is None
    # assert effects_sorted[2].prot_length is None
    assert effects_sorted[2].aa_change is None
