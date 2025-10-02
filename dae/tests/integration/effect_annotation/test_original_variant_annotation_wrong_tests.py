# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.effect_annotation.annotator import EffectAnnotator
from dae.genomic_resources.gene_models.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome


def test_chr1_120387132_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="1:120387132", variant="del(71)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "NBPF7"
    assert effect.transcript_id == "NM_001047980_1"
    assert effect.strand == "-"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 421
    assert effect.aa_change is None


def test_chr2_237172988_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="2:237172988", variant="ins(TTGTTACG)",
    )
    effect = effects[0]

    assert effect.gene == "ASB18"
    assert effect.transcript_id == "NM_212556_1"
    assert effect.strand == "-"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 466
    assert effect.aa_change is None


def test_chr1_802610_867930_cnv_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="1:802610-867930", variant="CNV+",
    )
    assert len(effects) == 3
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "SAMD11"
    assert effects_sorted[0].transcript_id == "NM_152486_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "CNV+"
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "LOC100130417"
    assert effects_sorted[1].transcript_id == "NR_026874_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "CNV+"
    assert effects_sorted[1].aa_change is None

    assert effects_sorted[2].gene == "FAM41C"
    assert effects_sorted[2].transcript_id == "NR_027055_1"
    assert effects_sorted[2].strand == "-"
    assert effects_sorted[2].effect == "CNV+"
    assert effects_sorted[2].aa_change is None
