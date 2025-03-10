# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines

from dae.effect_annotation.annotator import AnnotationEffect, EffectAnnotator
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome


def assert_chr1_897349_sub(effect: AnnotationEffect) -> None:
    assert effect.gene == "KLHL17"
    assert effect.transcript_id == "NM_198317_1"
    assert effect.strand == "+"
    assert effect.effect == "synonymous"
    assert effect.prot_pos == 211
    assert effect.prot_length == 642
    assert effect.aa_change == "Lys->Lys"


def test_synonymous_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:897349",
        variant="sub(G->A)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert_chr1_897349_sub(effect)


def test_synonymous_sub_ref_alt(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:897349",
        ref="G",
        alt="A",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert_chr1_897349_sub(effect)


def test_synonymous_sub_ref_alt_pos(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        chrom="1",
        position=897349,
        ref="G",
        alt="A",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert_chr1_897349_sub(effect)


def test_reverse_strand_frame_shift_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="1:3519050", variant="del(1)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "MEGF6"
    assert effect.transcript_id == "NM_001409_1"
    assert effect.strand == "-"
    assert effect.effect == "frame-shift"
    assert effect.prot_pos == 82
    assert effect.prot_length == 1541
    # assert effect.aa_change is None


def test_intron_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="1:53287094", variant="ins(G)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "ZYG11B"
    assert effect.transcript_id == "NM_024646_1"
    assert effect.strand == "+"
    assert effect.effect == "intron"
    assert effect.prot_pos == 682
    assert effect.prot_length == 744
    assert effect.aa_change is None
    assert effect.which_intron == 13
    assert effect.how_many_introns == 13
    assert effect.dist_from_coding == 17
    assert effect.dist_from_acceptor == 17
    assert effect.dist_from_donor == 4792
    assert effect.intron_length == 4809


def test_no_start_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="17:74729179",
        variant="del(3)",
    )

    assert len(effects) == 7
    for effect in effects:
        assert effect.gene == "METTL23"
        assert effect.strand == "+"

    effect = effects.pop(0)
    assert effect.transcript_id == "NM_001080510_1"
    assert effect.effect == "no-frame-shift"
    assert effect.prot_pos == 68
    assert effect.prot_length == 190
    assert effect.aa_change == "MetAsn->Ile"

    effect = effects.pop(0)
    assert effect.transcript_id == "NM_001206983_1"
    assert effect.effect == "no-frame-shift"
    assert effect.prot_pos == 68
    assert effect.prot_length == 190
    assert effect.aa_change == "MetAsn->Ile"

    effect = effects.pop(0)
    assert effect.transcript_id == "NM_001206984_1"
    assert effect.effect == "no-frame-shift"
    assert effect.prot_pos == 68
    assert effect.prot_length == 190
    assert effect.aa_change == "MetAsn->Ile"

    effect = effects.pop(0)
    assert effect.transcript_id == "NM_001206985_1"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 123
    assert effect.aa_change is None

    effect = effects.pop(0)
    assert effect.transcript_id == "NM_001206986_1"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 123
    assert effect.aa_change is None

    effect = effects.pop(0)
    assert effect.transcript_id == "NM_001206987_1"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 123
    assert effect.aa_change is None

    effect = effects.pop(0)
    assert effect.transcript_id == "NR_038193_1"
    assert effect.effect == "non-coding-intron"
    assert effect.prot_pos is None
    assert effect.prot_length is None
    assert effect.aa_change is None


def test_frame_shift_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="2:238617257",
        variant="ins(A)",
    )

    assert len(effects) == 5
    print(effects)

    effect = effects.pop(0)
    assert effect.gene == "LRRFIP1"
    assert effect.transcript_id == "NM_001137550_1"
    assert effect.strand == "+"
    assert effect.effect == "frame-shift"
    assert effect.prot_pos == 56
    assert effect.prot_length == 640
    # assert effect.aa_change is None

    effect = effects.pop(0)
    assert effect.gene == "LRRFIP1"
    assert effect.transcript_id == "NM_001137551_1"
    assert effect.strand == "+"
    assert effect.effect == "frame-shift"
    assert effect.prot_pos == 46
    assert effect.prot_length == 394
    # assert effect.aa_change is None

    effect = effects.pop(0)
    assert effect.gene == "LRRFIP1"
    assert effect.transcript_id == "NM_001137552_1"
    assert effect.strand == "+"
    assert effect.effect == "frame-shift"
    assert effect.prot_pos == 46
    assert effect.prot_length == 808
    # assert effect.aa_change is None

    effect = effects.pop(0)
    assert effect.gene == "LRRFIP1"
    assert effect.transcript_id == "NM_001137553_1"
    assert effect.strand == "+"
    assert effect.effect == "frame-shift"
    assert effect.prot_pos == 46
    assert effect.prot_length == 752
    # assert effect.aa_change is None

    effect = effects.pop(0)
    assert effect.gene == "LRRFIP1"
    assert effect.transcript_id == "NM_004735_1"
    assert effect.strand == "+"
    assert effect.effect == "frame-shift"
    assert effect.prot_pos == 46
    assert effect.prot_length == 784
    # assert effect.aa_change is None


def test_no_frame_shift_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="1:24507340", variant="del(3)",
    )

    assert len(effects) == 3

    effect = effects.pop(0)
    assert effect.gene == "IFNLR1"
    assert effect.transcript_id == "NM_170743_1"
    assert effect.strand == "-"
    assert effect.effect == "no-frame-shift"
    assert effect.prot_pos == 21
    assert effect.prot_length == 520
    assert effect.aa_change == "Arg->"

    effect = effects.pop(0)
    assert effect.gene == "IFNLR1"
    assert effect.transcript_id == "NM_173064_1"
    assert effect.strand == "-"
    assert effect.effect == "no-frame-shift"
    assert effect.prot_pos == 21
    assert effect.prot_length == 491
    assert effect.aa_change == "Arg->"

    effect = effects.pop(0)
    assert effect.gene == "IFNLR1"
    assert effect.transcript_id == "NM_173065_1"
    assert effect.strand == "-"
    assert effect.effect == "no-frame-shift"
    assert effect.prot_pos == 21
    assert effect.prot_length == 244
    assert effect.aa_change == "Arg->"


def test_nonsense_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:61553905",
        variant="sub(C->T)",
    )

    assert len(effects) == 4
    print(effects)

    effect = effects[0]
    assert effect.gene == "NFIA"
    assert effect.transcript_id == "NM_001134673_1"
    assert effect.strand == "+"
    assert effect.effect == "nonsense"
    assert effect.prot_pos == 38
    assert effect.prot_length == 509
    assert effect.aa_change == "Arg->End"

    effect = effects[1]
    assert effect.gene == "NFIA"
    assert effect.transcript_id == "NM_005595_1"
    assert effect.strand == "+"
    assert effect.effect == "nonsense"
    assert effect.prot_pos == 38
    assert effect.prot_length == 498
    assert effect.aa_change == "Arg->End"

    effect = effects[2]
    assert effect.gene == "NFIA"
    assert effect.transcript_id == "NM_001145511_1"
    assert effect.strand == "+"
    assert effect.effect == "nonsense"
    assert effect.prot_pos == 30
    assert effect.prot_length == 501
    assert effect.aa_change == "Arg->End"

    effect = effects[3]
    assert effect.gene == "NFIA"
    assert effect.transcript_id == "NM_001145512_1"
    assert effect.strand == "+"
    assert effect.effect == "nonsense"
    assert effect.prot_pos == 83
    assert effect.prot_length == 554
    assert effect.aa_change == "Arg->End"


def test_splice_site_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    # pylint: disable=too-many-statements
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:67878948",
        variant="sub(T->G)",
    )

    assert len(effects) == 4

    effect = effects[0]
    assert effect.gene == "SERBP1"
    assert effect.transcript_id == "NM_001018067_1"
    assert effect.strand == "-"
    assert effect.effect == "splice-site"
    assert effect.prot_pos == 391
    assert effect.prot_length == 408
    assert effect.aa_change is None
    assert effect.which_intron == 7
    assert effect.how_many_introns == 7
    assert effect.dist_from_coding == 1
    assert effect.dist_from_acceptor == 1
    assert effect.dist_from_donor == 1900
    assert effect.intron_length == 1902

    effect = effects[1]
    assert effect.gene == "SERBP1"
    assert effect.transcript_id == "NM_001018068_1"
    assert effect.strand == "-"
    assert effect.effect == "splice-site"
    assert effect.prot_pos == 385
    assert effect.prot_length == 402
    assert effect.aa_change is None
    assert effect.which_intron == 7
    assert effect.how_many_introns == 7
    assert effect.dist_from_coding == 1
    assert effect.dist_from_acceptor == 1
    assert effect.dist_from_donor == 1900
    assert effect.intron_length == 1902

    effect = effects[2]
    assert effect.gene == "SERBP1"
    assert effect.transcript_id == "NM_001018069_1"
    assert effect.strand == "-"
    assert effect.effect == "splice-site"
    assert effect.prot_pos == 376
    assert effect.prot_length == 393
    assert effect.aa_change is None
    assert effect.which_intron == 7
    assert effect.how_many_introns == 7
    assert effect.dist_from_coding == 1
    assert effect.dist_from_acceptor == 1
    assert effect.dist_from_donor == 1900
    assert effect.intron_length == 1902

    effect = effects[3]
    assert effect.gene == "SERBP1"
    assert effect.transcript_id == "NM_015640_1"
    assert effect.strand == "-"
    assert effect.effect == "splice-site"
    assert effect.prot_pos == 370
    assert effect.prot_length == 387
    assert effect.aa_change is None
    assert effect.which_intron == 7
    assert effect.how_many_introns == 7
    assert effect.dist_from_coding == 1
    assert effect.dist_from_acceptor == 1
    assert effect.dist_from_donor == 1900
    assert effect.intron_length == 1902


def test_no_frame_shift_newstop_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="17:17697260",
        variant="ins(AGT)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "RAI1"
    assert effect.transcript_id == "NM_030665_1"
    assert effect.strand == "+"
    assert effect.effect == "no-frame-shift-newStop"
    assert effect.prot_pos == 333
    assert effect.prot_length == 1906
    assert effect.aa_change == "Gln->GlnEnd"


def test_no_end_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="19:8645778", variant="del(9)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "ADAMTS10"
    assert effect.transcript_id == "NM_030957_1"
    assert effect.strand == "-"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 1101
    assert effect.prot_length == 1103
    assert effect.aa_change is None


def test_intergenic_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:20421037",
        variant="sub(G->A)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene is None
    assert effect.transcript_id is None
    assert effect.strand is None
    assert effect.effect == "intergenic"
    assert effect.prot_pos is None
    assert effect.prot_length is None
    assert effect.aa_change is None


def test_3_utr_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:47013144",
        variant="sub(G->A)",
    )

    assert len(effects) == 2

    assert effects[0].gene == "KNCN"
    assert effects[0].transcript_id == "NM_001097611_1"
    assert effects[0].strand == "-"
    assert effects[0].effect == "3'UTR"
    assert effects[0].prot_pos is None
    assert effects[0].prot_length == 101
    assert effects[0].aa_change is None
    assert effects[0].dist_from_coding == 258

    assert effects[1].gene == "MKNK1-AS1"
    assert effects[1].transcript_id == "NR_038403_1"
    assert effects[1].strand == "+"
    assert effects[1].effect == "non-coding-intron"
    assert effects[1].prot_pos is None
    assert effects[1].prot_length is None
    assert effects[1].aa_change is None


def test_5_utr_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:57284965",
        variant="sub(G->A)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "C1orf168"
    assert effect.transcript_id == "NM_001004303_1"
    assert effect.strand == "-"
    assert effect.effect == "5'UTR"
    assert effect.prot_pos is None
    assert effect.prot_length == 728
    assert effect.aa_change is None
    assert effect.dist_from_coding == 2


def test_middle_codon_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:897348",
        variant="sub(A->G)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "KLHL17"
    assert effect.transcript_id == "NM_198317_1"
    assert effect.strand == "+"
    assert effect.effect == "missense"
    assert effect.prot_pos == 211
    assert effect.prot_length == 642
    assert effect.aa_change == "Lys->Arg"


def test_splice_site_del_pos_strand_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="7:24720141", variant="del(1)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "MPP6"
    assert effect.transcript_id == "NM_016447_1"
    assert effect.strand == "+"
    assert effect.effect == "splice-site"
    assert effect.prot_pos == 483
    assert effect.prot_length == 540
    assert effect.aa_change is None
    assert effect.which_intron == 12
    assert effect.how_many_introns == 12
    assert effect.dist_from_coding == 1
    assert effect.dist_from_acceptor == 6915
    assert effect.dist_from_donor == 1
    assert effect.intron_length == 6917


def test_splice_site_del_neg_strand_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="4:48523230", variant="del(4)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "FRYL"
    assert effect.transcript_id == "NM_015030_1"
    assert effect.strand == "-"
    assert effect.effect == "splice-site"
    assert effect.prot_pos == 2508
    assert effect.prot_length == 3013
    assert effect.aa_change is None
    assert effect.which_intron == 54
    assert effect.how_many_introns == 63
    assert effect.dist_from_coding == -3
    assert effect.dist_from_acceptor == -3
    assert effect.dist_from_donor == 1684
    assert effect.intron_length == 1685


def test_splice_site_ins_pos_strand_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="7:24720141", variant="ins(C)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "MPP6"
    assert effect.transcript_id == "NM_016447_1"
    assert effect.strand == "+"
    assert effect.effect == "splice-site"
    assert effect.prot_pos == 483
    assert effect.prot_length == 540
    assert effect.aa_change is None
    assert effect.which_intron == 12
    assert effect.how_many_introns == 12
    assert effect.dist_from_coding == 1
    assert effect.dist_from_acceptor == 6916
    assert effect.dist_from_donor == 1
    assert effect.intron_length == 6917


def test_splice_site_ins_neg_strand_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="12:116418554",
        variant="ins(C)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "MED13L"
    assert effect.transcript_id == "NM_015335_1"
    assert effect.strand == "-"
    assert effect.effect == "splice-site"
    assert effect.prot_pos == 1789
    assert effect.prot_length == 2210
    assert effect.aa_change is None
    assert effect.which_intron == 23
    assert effect.how_many_introns == 30
    assert effect.dist_from_coding == 1
    assert effect.dist_from_acceptor == 5010
    assert effect.dist_from_donor == 1
    assert effect.intron_length == 5011


def test_first_codon_ins_noend_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="1:3407093", variant="ins(A)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "MEGF6"
    assert effect.transcript_id == "NM_001409_1"
    assert effect.strand == "-"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 1542
    assert effect.prot_length == 1541
    assert effect.aa_change is None


def test_first_codon_sub_nostart_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="7:24663287",
        variant="sub(T->C)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "MPP6"
    assert effect.transcript_id == "NM_016447_1"
    assert effect.strand == "+"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 540
    assert effect.aa_change is None


def test_last_codon_sub_nostop_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="7:24727231",
        variant="sub(T->C)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "MPP6"
    assert effect.transcript_id == "NM_016447_1"
    assert effect.strand == "+"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 541
    assert effect.prot_length == 540
    assert effect.aa_change is None


def test_chr1_71418630_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    # pylint: disable=too-many-statements
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:71418630",
        variant="sub(A->G)",
    )

    assert len(effects) == 8
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "PTGER3"
    assert effects_sorted[0].transcript_id == "NM_001126044_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "3'UTR"
    assert effects_sorted[0].prot_pos is None
    assert effects_sorted[0].prot_length == 390
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].dist_from_coding == 136

    assert effects_sorted[1].gene == "PTGER3"
    assert effects_sorted[1].transcript_id == "NM_198714_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "3'UTR-intron"
    assert effects_sorted[1].prot_pos is None
    assert effects_sorted[1].prot_length == 390
    assert effects_sorted[1].aa_change is None

    assert effects_sorted[2].gene == "PTGER3"
    assert effects_sorted[2].transcript_id == "NM_198716_1"
    assert effects_sorted[2].strand == "-"
    assert effects_sorted[2].effect == "intron"
    assert effects_sorted[2].prot_pos == 369
    assert effects_sorted[2].prot_length == 374
    assert effects_sorted[2].aa_change is None
    assert effects_sorted[2].which_intron == 3
    assert effects_sorted[2].how_many_introns == 3
    assert effects_sorted[2].dist_from_coding == 815
    assert effects_sorted[2].dist_from_acceptor == 100087
    assert effects_sorted[2].dist_from_donor == 815
    assert effects_sorted[2].intron_length == 100903

    assert effects_sorted[3].gene == "PTGER3"
    assert effects_sorted[3].transcript_id == "NM_198717_1"
    assert effects_sorted[3].strand == "-"
    assert effects_sorted[3].effect == "intron"
    assert effects_sorted[3].prot_pos == 360
    assert effects_sorted[3].prot_length == 365
    assert effects_sorted[3].aa_change is None
    assert effects_sorted[3].which_intron == 2
    assert effects_sorted[3].how_many_introns == 2
    assert effects_sorted[3].dist_from_coding == 59357
    assert effects_sorted[3].dist_from_acceptor == 100087
    assert effects_sorted[3].dist_from_donor == 59357
    assert effects_sorted[3].intron_length == 159445

    assert effects_sorted[4].gene == "PTGER3"
    assert effects_sorted[4].transcript_id == "NM_198718_1"
    assert effects_sorted[4].strand == "-"
    assert effects_sorted[4].effect == "missense"
    assert effects_sorted[4].prot_pos == 406
    assert effects_sorted[4].prot_length == 418
    assert effects_sorted[4].aa_change == "Ile->Thr"

    assert effects_sorted[5].gene == "PTGER3"
    assert effects_sorted[5].transcript_id == "NR_028292_1"
    assert effects_sorted[5].strand == "-"
    assert effects_sorted[5].effect == "non-coding-intron"
    assert effects_sorted[5].prot_pos is None
    assert effects_sorted[5].prot_length is None
    assert effects_sorted[5].aa_change is None

    assert effects_sorted[6].gene == "PTGER3"
    assert effects_sorted[6].transcript_id == "NR_028293_1"
    assert effects_sorted[6].strand == "-"
    assert effects_sorted[6].effect == "non-coding-intron"
    assert effects_sorted[6].prot_pos is None
    assert effects_sorted[6].prot_length is None
    assert effects_sorted[6].aa_change is None

    assert effects_sorted[7].gene == "PTGER3"
    assert effects_sorted[7].transcript_id == "NR_028294_1"
    assert effects_sorted[7].strand == "-"
    assert effects_sorted[7].effect == "non-coding-intron"
    assert effects_sorted[7].prot_pos is None
    assert effects_sorted[7].prot_length is None
    assert effects_sorted[7].aa_change is None


def test_chr20_56284593_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="20:56284593",
        variant="ins(CGGCGG)",
    )

    assert len(effects) == 4
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "PMEPA1"
    assert effects_sorted[0].transcript_id == "NM_020182_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "no-frame-shift"
    assert effects_sorted[0].prot_pos == 16
    assert effects_sorted[0].prot_length == 287
    assert effects_sorted[0].aa_change == "Gly->AlaAlaGly"

    assert effects_sorted[1].gene == "PMEPA1"
    assert effects_sorted[1].transcript_id == "NM_199169_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "intron"
    assert effects_sorted[1].prot_pos == 2
    assert effects_sorted[1].prot_length == 252
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].which_intron == 1
    assert effects_sorted[1].how_many_introns == 3
    assert effects_sorted[1].dist_from_coding == 923
    assert effects_sorted[1].dist_from_acceptor == 49839
    assert effects_sorted[1].dist_from_donor == 923
    assert effects_sorted[1].intron_length == 50762

    assert effects_sorted[2].gene == "PMEPA1"
    assert effects_sorted[2].transcript_id == "NM_199170_1"
    assert effects_sorted[2].strand == "-"
    assert effects_sorted[2].effect == "5'UTR-intron"
    assert effects_sorted[2].prot_pos is None
    assert effects_sorted[2].prot_length == 237
    assert effects_sorted[2].aa_change is None

    assert effects_sorted[3].gene == "PMEPA1"
    assert effects_sorted[3].transcript_id == "NM_199171_1"
    assert effects_sorted[3].strand == "-"
    assert effects_sorted[3].effect == "5'UTR-intron"
    assert effects_sorted[3].prot_pos is None
    assert effects_sorted[3].prot_length == 237
    assert effects_sorted[3].aa_change is None


def test_chr20_57478739_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    # pylint: disable=too-many-statements
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="20:57478739",
        variant="sub(G->A)",
    )

    assert len(effects) == 8
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "GNAS"
    assert effects_sorted[0].transcript_id == "NM_000516_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "missense"
    assert effects_sorted[0].prot_pos == 109
    assert effects_sorted[0].prot_length == 394
    assert effects_sorted[0].aa_change == "Ala->Thr"

    assert effects_sorted[1].gene == "GNAS"
    assert effects_sorted[1].transcript_id == "NM_001077488_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "missense"
    assert effects_sorted[1].prot_pos == 110
    assert effects_sorted[1].prot_length == 395
    assert effects_sorted[1].aa_change == "Ala->Thr"

    assert effects_sorted[2].gene == "GNAS"
    assert effects_sorted[2].transcript_id == "NM_001077489_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "missense"
    assert effects_sorted[2].prot_pos == 94
    assert effects_sorted[2].prot_length == 379
    assert effects_sorted[2].aa_change == "Ala->Thr"

    assert effects_sorted[3].gene == "GNAS"
    assert effects_sorted[3].transcript_id == "NM_001077490_1"
    assert effects_sorted[3].strand == "+"
    assert effects_sorted[3].effect == "3'UTR"
    assert effects_sorted[3].prot_pos is None
    assert effects_sorted[3].prot_length == 626
    assert effects_sorted[3].aa_change is None
    assert effects_sorted[3].dist_from_coding == 186

    assert effects_sorted[4].gene == "GNAS"
    assert effects_sorted[4].transcript_id == "NM_016592_1"
    assert effects_sorted[4].strand == "+"
    assert effects_sorted[4].effect == "3'UTR"
    assert effects_sorted[4].prot_pos is None
    assert effects_sorted[4].prot_length == 245
    assert effects_sorted[4].aa_change is None
    assert effects_sorted[4].dist_from_coding == 231

    assert effects_sorted[5].gene == "GNAS"
    assert effects_sorted[5].transcript_id == "NM_080425_1"
    assert effects_sorted[5].strand == "+"
    assert effects_sorted[5].effect == "missense"
    assert effects_sorted[5].prot_pos == 752
    assert effects_sorted[5].prot_length == 1037
    assert effects_sorted[5].aa_change == "Ala->Thr"

    assert effects_sorted[6].gene == "GNAS"
    assert effects_sorted[6].transcript_id == "NM_080426_1"
    assert effects_sorted[6].strand == "+"
    assert effects_sorted[6].effect == "missense"
    assert effects_sorted[6].prot_pos == 95
    assert effects_sorted[6].prot_length == 380
    assert effects_sorted[6].aa_change == "Ala->Thr"

    assert effects_sorted[7].gene == "GNAS"
    assert effects_sorted[7].transcript_id == "NR_003259_1"
    assert effects_sorted[7].strand == "+"
    assert effects_sorted[7].effect == "non-coding"
    assert effects_sorted[7].prot_pos is None
    assert effects_sorted[7].prot_length is None
    assert effects_sorted[7].aa_change is None


def test_chr14_78227471_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="14:78227471",
        variant="del(9)",
    )

    assert len(effects) == 3
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "C14orf178"
    assert effects_sorted[0].transcript_id == "NM_001173978_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "5'UTR-intron"
    assert effects_sorted[0].prot_pos is None
    assert effects_sorted[0].prot_length == 92
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "SNW1"
    assert effects_sorted[1].transcript_id == "NM_012245_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "5'UTR"
    assert effects_sorted[1].prot_pos is None
    assert effects_sorted[1].prot_length == 536
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].dist_from_coding == 1

    assert effects_sorted[2].gene == "C14orf178"
    assert effects_sorted[2].transcript_id == "NM_174943_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "intron"
    assert effects_sorted[2].prot_pos == 25
    assert effects_sorted[2].prot_length == 122
    assert effects_sorted[2].aa_change is None
    assert effects_sorted[2].which_intron == 1
    assert effects_sorted[2].how_many_introns == 2
    assert effects_sorted[2].dist_from_coding == 11
    assert effects_sorted[2].dist_from_acceptor == 7315
    assert effects_sorted[2].dist_from_donor == 11
    assert effects_sorted[2].intron_length == 7335


def test_chr3_128813981_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    # pylint: disable=too-many-statements
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="3:128813981",
        variant="sub(C->T)",
    )

    assert len(effects) == 8
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "RAB43"
    assert effects_sorted[0].transcript_id == "NM_001204883_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "missense"
    assert effects_sorted[0].prot_pos == 79
    assert effects_sorted[0].prot_length == 212
    assert effects_sorted[0].aa_change == "Arg->Gln"

    assert effects_sorted[1].gene == "RAB43"
    assert effects_sorted[1].transcript_id == "NM_001204884_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "missense"
    assert effects_sorted[1].prot_pos == 79
    assert effects_sorted[1].prot_length == 212
    assert effects_sorted[1].aa_change == "Arg->Gln"

    assert effects_sorted[2].gene == "RAB43"
    assert effects_sorted[2].transcript_id == "NM_001204885_1"
    assert effects_sorted[2].strand == "-"
    assert effects_sorted[2].effect == "missense"
    assert effects_sorted[2].prot_pos == 79
    assert effects_sorted[2].prot_length == 212
    assert effects_sorted[2].aa_change == "Arg->Gln"

    assert effects_sorted[3].gene == "RAB43"
    assert effects_sorted[3].transcript_id == "NM_001204886_1"
    assert effects_sorted[3].strand == "-"
    assert effects_sorted[3].effect == "missense"
    assert effects_sorted[3].prot_pos == 79
    assert effects_sorted[3].prot_length == 212
    assert effects_sorted[3].aa_change == "Arg->Gln"

    assert effects_sorted[4].gene == "RAB43"
    assert effects_sorted[4].transcript_id == "NM_001204887_1"
    assert effects_sorted[4].strand == "-"
    assert effects_sorted[4].effect == "missense"
    assert effects_sorted[4].prot_pos == 79
    assert effects_sorted[4].prot_length == 155
    assert effects_sorted[4].aa_change == "Arg->Gln"

    assert effects_sorted[5].gene == "RAB43"
    assert effects_sorted[5].transcript_id == "NM_001204888_1"
    assert effects_sorted[5].strand == "-"
    assert effects_sorted[5].effect == "synonymous"
    assert effects_sorted[5].prot_pos == 74
    assert effects_sorted[5].prot_length == 108
    assert effects_sorted[5].aa_change == "Ala->Ala"

    assert effects_sorted[6].gene == "ISY1-RAB43"
    assert effects_sorted[6].transcript_id == "NM_001204890_1"
    assert effects_sorted[6].strand == "-"
    assert effects_sorted[6].effect == "missense"
    assert effects_sorted[6].prot_pos == 295
    assert effects_sorted[6].prot_length == 331
    assert effects_sorted[6].aa_change == "Gly->Ser"

    assert effects_sorted[7].gene == "RAB43"
    assert effects_sorted[7].transcript_id == "NM_198490_1"
    assert effects_sorted[7].strand == "-"
    assert effects_sorted[7].effect == "missense"
    assert effects_sorted[7].prot_pos == 79
    assert effects_sorted[7].prot_length == 212
    assert effects_sorted[7].aa_change == "Arg->Gln"


def test_chr14_21895990_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="14:21895990",
        variant="del(47)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "CHD8"
    assert effects_sorted[0].transcript_id == "NM_001170629_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "splice-site"
    assert effects_sorted[0].prot_pos == 534
    assert effects_sorted[0].prot_length == 2581
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 3
    assert effects_sorted[0].how_many_introns == 36
    assert effects_sorted[0].dist_from_coding == -9
    assert effects_sorted[0].dist_from_acceptor == 1588
    assert effects_sorted[0].dist_from_donor == -9
    assert effects_sorted[0].intron_length == 1626

    assert effects_sorted[1].gene == "CHD8"
    assert effects_sorted[1].transcript_id == "NM_020920_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "splice-site"
    assert effects_sorted[1].prot_pos == 255
    assert effects_sorted[1].prot_length == 2302
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].which_intron == 4
    assert effects_sorted[1].how_many_introns == 37
    assert effects_sorted[1].dist_from_coding == -9
    assert effects_sorted[1].dist_from_acceptor == 1588
    assert effects_sorted[1].dist_from_donor == -9
    assert effects_sorted[1].intron_length == 1626


def test_chr1_12175787_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:12175787",
        variant="sub(G->A)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "TNFRSF8"
    assert effects_sorted[0].transcript_id == "NM_001243_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "splice-site"
    assert effects_sorted[0].prot_pos == 316
    assert effects_sorted[0].prot_length == 595
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 8
    assert effects_sorted[0].how_many_introns == 14
    assert effects_sorted[0].dist_from_coding == 0
    assert effects_sorted[0].dist_from_acceptor == 7553
    assert effects_sorted[0].dist_from_donor == 0
    assert effects_sorted[0].intron_length == 7554

    assert effects_sorted[1].gene == "TNFRSF8"
    assert effects_sorted[1].transcript_id == "NM_001281430_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "splice-site"
    assert effects_sorted[1].prot_pos == 205
    assert effects_sorted[1].prot_length == 483
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].which_intron == 7
    assert effects_sorted[1].how_many_introns == 13
    assert effects_sorted[1].dist_from_coding == 0
    assert effects_sorted[1].dist_from_acceptor == 7553
    assert effects_sorted[1].dist_from_donor == 0
    assert effects_sorted[1].intron_length == 7554


def test_chr13_23904276_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="13:23904276",
        variant="sub(C->T)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "SACS"
    assert effects_sorted[0].transcript_id == "NM_001278055_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "synonymous"
    assert effects_sorted[0].prot_pos == 4433
    assert effects_sorted[0].prot_length == 4432
    assert effects_sorted[0].aa_change == "End->End"

    assert effects_sorted[1].gene == "SACS"
    assert effects_sorted[1].transcript_id == "NM_014363_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "synonymous"
    assert effects_sorted[1].prot_pos == 4580
    assert effects_sorted[1].prot_length == 4579
    assert effects_sorted[1].aa_change == "End->End"


def test_chr20_61476990_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="20:61476990",
        variant="del(3)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "TCFL5"
    assert effects_sorted[0].transcript_id == "NM_006602_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "intron"
    assert effects_sorted[0].prot_pos == 461
    assert effects_sorted[0].prot_length == 500
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 5
    assert effects_sorted[0].how_many_introns == 5
    assert effects_sorted[0].dist_from_coding == 3540
    assert effects_sorted[0].dist_from_acceptor == 3540
    assert effects_sorted[0].dist_from_donor == 8375
    assert effects_sorted[0].intron_length == 11918

    assert effects_sorted[1].gene == "DPH3P1"
    assert effects_sorted[1].transcript_id == "NM_080750_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "5'UTR"
    assert effects_sorted[1].prot_pos is None
    assert effects_sorted[1].prot_length == 78
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].dist_from_coding == 24


def test_chr17_43227526_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="17:43227526",
        variant="ins(GGAGCT)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "HEXIM1"
    assert effect.transcript_id == "NM_006460_1"
    assert effect.strand == "+"
    assert effect.effect == "no-frame-shift"
    assert effect.prot_pos == 323
    assert effect.prot_length == 359
    assert effect.aa_change == "Arg->ArgGluLeu"


def test_chr5_56527122_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="5:56527122",
        variant="sub(C->T)",
    )

    assert len(effects) == 4
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "GPBP1"
    assert effects_sorted[0].transcript_id == "NM_001127235_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "missense"
    assert effects_sorted[0].prot_pos == 136
    assert effects_sorted[0].prot_length == 465
    assert effects_sorted[0].aa_change == "Arg->Cys"

    assert effects_sorted[1].gene == "GPBP1"
    assert effects_sorted[1].transcript_id == "NM_001127236_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "missense"
    assert effects_sorted[1].prot_pos == 136
    assert effects_sorted[1].prot_length == 480
    assert effects_sorted[1].aa_change == "Arg->Cys"

    assert effects_sorted[2].gene == "GPBP1"
    assert effects_sorted[2].transcript_id == "NM_001203246_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "5'UTR"
    assert effects_sorted[2].prot_pos is None
    assert effects_sorted[2].prot_length == 302
    assert effects_sorted[2].aa_change is None
    assert effects_sorted[2].dist_from_coding == 129

    assert effects_sorted[3].gene == "GPBP1"
    assert effects_sorted[3].transcript_id == "NM_022913_1"
    assert effects_sorted[3].strand == "+"
    assert effects_sorted[3].effect == "missense"
    assert effects_sorted[3].prot_pos == 129
    assert effects_sorted[3].prot_length == 473
    assert effects_sorted[3].aa_change == "Arg->Cys"


def test_chr4_2514166_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="4:2514166", variant="del(3)",
    )

    assert len(effects) == 3
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "RNF4"
    assert effects_sorted[0].transcript_id == "NM_001185009_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "no-frame-shift"
    assert effects_sorted[0].prot_pos == 72
    assert effects_sorted[0].prot_length == 190
    assert effects_sorted[0].aa_change == "GluArg->Glu"

    assert effects_sorted[1].gene == "RNF4"
    assert effects_sorted[1].transcript_id == "NM_001185010_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "intron"
    assert effects_sorted[1].prot_pos == 72
    assert effects_sorted[1].prot_length == 113
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].which_intron == 5
    assert effects_sorted[1].how_many_introns == 6
    assert effects_sorted[1].dist_from_coding == 473
    assert effects_sorted[1].dist_from_acceptor == 641
    assert effects_sorted[1].dist_from_donor == 473
    assert effects_sorted[1].intron_length == 1117

    assert effects_sorted[2].gene == "RNF4"
    assert effects_sorted[2].transcript_id == "NM_002938_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "no-frame-shift"
    assert effects_sorted[2].prot_pos == 72
    assert effects_sorted[2].prot_length == 190
    assert effects_sorted[2].aa_change == "GluArg->Glu"


def test_chr7_131870222_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="7:131870222",
        variant="sub(C->A)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "PLXNA4"
    assert effect.transcript_id == "NM_020911_1"
    assert effect.strand == "-"
    assert effect.effect == "missense"
    assert effect.prot_pos == 998
    assert effect.prot_length == 1894
    assert effect.aa_change == "Arg->Ser"


def test_chr6_107780195_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="6:107780195",
        variant="sub(T->A)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "PDSS2"
    assert effect.transcript_id == "NM_020381_1"
    assert effect.strand == "-"
    assert effect.effect == "missense"
    assert effect.prot_pos == 99
    assert effect.prot_length == 399
    assert effect.aa_change == "Arg->Trp"


def test_chr15_80137554_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="15:80137554",
        variant="ins(A)",
    )

    assert len(effects) == 4
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "MTHFS"
    assert effects_sorted[0].transcript_id == "NM_001199758_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "noEnd"
    assert effects_sorted[0].prot_pos == 147
    assert effects_sorted[0].prot_length == 146
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "ST20-MTHFS"
    assert effects_sorted[1].transcript_id == "NM_001199760_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "noEnd"
    assert effects_sorted[1].prot_pos == 180
    assert effects_sorted[1].prot_length == 179
    assert effects_sorted[1].aa_change is None

    assert effects_sorted[2].gene == "MTHFS"
    assert effects_sorted[2].transcript_id == "NM_006441_1"
    assert effects_sorted[2].strand == "-"
    assert effects_sorted[2].effect == "noEnd"
    assert effects_sorted[2].prot_pos == 204
    assert effects_sorted[2].prot_length == 203
    assert effects_sorted[2].aa_change is None

    assert effects_sorted[3].gene == "MTHFS"
    assert effects_sorted[3].transcript_id == "NR_037654_1"
    assert effects_sorted[3].strand == "-"
    assert effects_sorted[3].effect == "non-coding"
    assert effects_sorted[3].prot_pos is None
    assert effects_sorted[3].prot_length is None
    assert effects_sorted[3].aa_change is None


def test_chr1_207793410_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:207793410",
        variant="sub(C->T)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "CR1"
    assert effects_sorted[0].transcript_id == "NM_000573_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "missense"
    assert effects_sorted[0].prot_pos == 1968
    assert effects_sorted[0].prot_length == 2039
    assert effects_sorted[0].aa_change == "Arg->Cys"

    assert effects_sorted[1].gene == "CR1"
    assert effects_sorted[1].transcript_id == "NM_000651_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "missense"
    assert effects_sorted[1].prot_pos == 2418
    assert effects_sorted[1].prot_length == 2489
    assert effects_sorted[1].aa_change == "Arg->Cys"


def test_chr3_49051816_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="3:49051816",
        variant="sub(G->A)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "WDR6"
    assert effect.transcript_id == "NM_018031_1"
    assert effect.strand == "+"
    assert effect.effect == "synonymous"
    assert effect.prot_pos == 919
    assert effect.prot_length == 1151
    assert effect.aa_change == "Arg->Arg"


def test_chr5_79855195_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="5:79855195", variant="del(6)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "ANKRD34B"
    assert effect.transcript_id == "NM_001004441_1"
    assert effect.strand == "-"
    assert effect.effect == "no-frame-shift"
    assert effect.prot_pos == 213
    assert effect.prot_length == 514
    assert effect.aa_change == "AspLeuGlu->Glu"


def test_chr3_112997521_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="3:112997521",
        variant="sub(A->T)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "BOC"
    assert effect.transcript_id == "NM_033254_1"
    assert effect.strand == "+"
    assert effect.effect == "synonymous"
    assert effect.prot_pos == 568
    assert effect.prot_length == 1114
    assert effect.aa_change == "Gly->Gly"


def test_chr2_169417831_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="2:169417831",
        variant="sub(A->G)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "CERS6"
    assert effects_sorted[0].transcript_id == "NM_001256126_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "missense"
    assert effects_sorted[0].prot_pos == 136
    assert effects_sorted[0].prot_length == 392
    assert effects_sorted[0].aa_change == "Met->Val"

    assert effects_sorted[1].gene == "CERS6"
    assert effects_sorted[1].transcript_id == "NM_203463_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "missense"
    assert effects_sorted[1].prot_pos == 136
    assert effects_sorted[1].prot_length == 384
    assert effects_sorted[1].aa_change == "Met->Val"


def test_chr2_170062840_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="2:170062840",
        variant="sub(C->T)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "LRP2"
    assert effect.transcript_id == "NM_004525_1"
    assert effect.strand == "-"
    assert effect.effect == "missense"
    assert effect.prot_pos == 2464
    assert effect.prot_length == 4655
    assert effect.aa_change == "Gly->Ser"


def test_chr17_72954572_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="17:72954572",
        variant="sub(A->T)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "HID1"
    assert effect.transcript_id == "NM_030630_1"
    assert effect.strand == "-"
    assert effect.effect == "synonymous"
    assert effect.prot_pos == 414
    assert effect.prot_length == 788
    assert effect.aa_change == "Ser->Ser"


def test_chr4_140640596_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="4:140640596",
        variant="sub(C->T)",
    )

    assert len(effects) == 3
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "MGST2"
    assert effects_sorted[0].transcript_id == "NM_001204366_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "3'UTR-intron"
    assert effects_sorted[0].prot_pos is None
    assert effects_sorted[0].prot_length == 147
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "MGST2"
    assert effects_sorted[1].transcript_id == "NM_001204367_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "3'UTR-intron"
    assert effects_sorted[1].prot_pos is None
    assert effects_sorted[1].prot_length == 79
    assert effects_sorted[1].aa_change is None

    assert effects_sorted[2].gene == "MAML3"
    assert effects_sorted[2].transcript_id == "NM_018717_1"
    assert effects_sorted[2].strand == "-"
    assert effects_sorted[2].effect == "missense"
    assert effects_sorted[2].prot_pos == 1096
    assert effects_sorted[2].prot_length == 1134
    assert effects_sorted[2].aa_change == "Gly->Arg"


def test_chr7_40134547_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="7:40134547",
        variant="ins(GGCAGA)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "CDK13"
    assert effects_sorted[0].transcript_id == "NM_003718_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "no-frame-shift"
    assert effects_sorted[0].prot_pos == 1503
    assert effects_sorted[0].prot_length == 1512
    assert effects_sorted[0].aa_change == "->GlyArg"

    assert effects_sorted[1].gene == "CDK13"
    assert effects_sorted[1].transcript_id == "NM_031267_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "no-frame-shift"
    assert effects_sorted[1].prot_pos == 1443
    assert effects_sorted[1].prot_length == 1452
    assert effects_sorted[1].aa_change == "->GlyArg"


def test_chr9_98279102_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="9:98279102",
        variant="sub(T->G)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "PTCH1"
    assert effects_sorted[0].transcript_id == "NM_001083602_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "5'UTR"
    assert effects_sorted[0].prot_pos is None
    assert effects_sorted[0].prot_length == 1381
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].dist_from_coding == 349

    assert effects_sorted[1].gene == "PTCH1"
    assert effects_sorted[1].transcript_id == "NM_001083603_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "noStart"
    assert effects_sorted[1].prot_pos == 1
    assert effects_sorted[1].prot_length == 1446
    assert effects_sorted[1].aa_change is None


def test_chr2_166535661_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="2:166535661",
        variant="del(3)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "CSRNP3"
    assert effects_sorted[0].transcript_id == "NM_001172173_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "no-frame-shift"
    assert effects_sorted[0].prot_pos == 386
    assert effects_sorted[0].prot_length == 585
    assert effects_sorted[0].aa_change == "Asp->"

    assert effects_sorted[1].gene == "CSRNP3"
    assert effects_sorted[1].transcript_id == "NM_024969_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "no-frame-shift"
    assert effects_sorted[1].prot_pos == 386
    assert effects_sorted[1].prot_length == 585
    assert effects_sorted[1].aa_change == "Asp->"


def test_chr4_76734406_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="4:76734406",
        variant="sub(T->C)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "USO1"
    assert effect.transcript_id == "NM_003715_1"
    assert effect.strand == "+"
    assert effect.effect == "synonymous"
    assert effect.prot_pos == 899
    assert effect.prot_length == 912
    assert effect.aa_change == "Asp->Asp"


def test_chr12_70824294_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="12:70824294",
        variant="del(3)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "KCNMB4"
    assert effect.transcript_id == "NM_014505_1"
    assert effect.strand == "+"
    assert effect.effect == "no-frame-shift"
    assert effect.prot_pos == 165
    assert effect.prot_length == 210
    assert effect.aa_change == "HisAsp->His"


def test_chr20_34243229_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    # pylint: disable=too-many-statements
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="20:34243229",
        variant="sub(G->A)",
    )

    assert len(effects) == 10
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "RBM12"
    assert effects_sorted[0].transcript_id == "NM_001198838_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "missense"
    assert effects_sorted[0].prot_pos == 6
    assert effects_sorted[0].prot_length == 932
    assert effects_sorted[0].aa_change == "Arg->Cys"

    assert effects_sorted[1].gene == "RBM12"
    assert effects_sorted[1].transcript_id == "NM_001198840_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "missense"
    assert effects_sorted[1].prot_pos == 6
    assert effects_sorted[1].prot_length == 932
    assert effects_sorted[1].aa_change == "Arg->Cys"

    assert effects_sorted[2].gene == "CPNE1"
    assert effects_sorted[2].transcript_id == "NM_001198863_1"
    assert effects_sorted[2].strand == "-"
    assert effects_sorted[2].effect == "5'UTR-intron"
    assert effects_sorted[2].prot_pos is None
    assert effects_sorted[2].prot_length == 536
    assert effects_sorted[2].aa_change is None

    assert effects_sorted[3].gene == "RBM12"
    assert effects_sorted[3].transcript_id == "NM_006047_1"
    assert effects_sorted[3].strand == "-"
    assert effects_sorted[3].effect == "missense"
    assert effects_sorted[3].prot_pos == 6
    assert effects_sorted[3].prot_length == 932
    assert effects_sorted[3].aa_change == "Arg->Cys"

    assert effects_sorted[4].gene == "RBM12"
    assert effects_sorted[4].transcript_id == "NM_152838_1"
    assert effects_sorted[4].strand == "-"
    assert effects_sorted[4].effect == "missense"
    assert effects_sorted[4].prot_pos == 6
    assert effects_sorted[4].prot_length == 932
    assert effects_sorted[4].aa_change == "Arg->Cys"

    assert effects_sorted[5].gene == "CPNE1"
    assert effects_sorted[5].transcript_id == "NM_152925_1"
    assert effects_sorted[5].strand == "-"
    assert effects_sorted[5].effect == "5'UTR-intron"
    assert effects_sorted[5].prot_pos is None
    assert effects_sorted[5].prot_length == 537
    assert effects_sorted[5].aa_change is None

    assert effects_sorted[6].gene == "CPNE1"
    assert effects_sorted[6].transcript_id == "NM_152926_1"
    assert effects_sorted[6].strand == "-"
    assert effects_sorted[6].effect == "5'UTR-intron"
    assert effects_sorted[6].prot_pos is None
    assert effects_sorted[6].prot_length == 537
    assert effects_sorted[6].aa_change is None

    assert effects_sorted[7].gene == "CPNE1"
    assert effects_sorted[7].transcript_id == "NM_152927_1"
    assert effects_sorted[7].strand == "-"
    assert effects_sorted[7].effect == "5'UTR-intron"
    assert effects_sorted[7].prot_pos is None
    assert effects_sorted[7].prot_length == 537
    assert effects_sorted[7].aa_change is None

    assert effects_sorted[8].gene == "CPNE1"
    assert effects_sorted[8].transcript_id == "NM_152928_1"
    assert effects_sorted[8].strand == "-"
    assert effects_sorted[8].effect == "5'UTR-intron"
    assert effects_sorted[8].prot_pos is None
    assert effects_sorted[8].prot_length == 537
    assert effects_sorted[8].aa_change is None

    assert effects_sorted[9].gene == "CPNE1"
    assert effects_sorted[9].transcript_id == "NR_037188_1"
    assert effects_sorted[9].strand == "-"
    assert effects_sorted[9].effect == "non-coding"
    assert effects_sorted[9].prot_pos is None
    assert effects_sorted[9].prot_length is None
    assert effects_sorted[9].aa_change is None


def test_chr7_6505720_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="7:6505720", variant="del(3)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "KDELR2"
    assert effects_sorted[0].transcript_id == "NM_001100603_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "intron"
    assert effects_sorted[0].prot_pos == 118
    assert effects_sorted[0].prot_length == 186
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 3
    assert effects_sorted[0].how_many_introns == 3
    assert effects_sorted[0].dist_from_coding == 2913
    assert effects_sorted[0].dist_from_acceptor == 2913
    assert effects_sorted[0].dist_from_donor == 3504
    assert effects_sorted[0].intron_length == 6420

    assert effects_sorted[1].gene == "KDELR2"
    assert effects_sorted[1].transcript_id == "NM_006854_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "no-frame-shift"
    assert effects_sorted[1].prot_pos == 195
    assert effects_sorted[1].prot_length == 212
    assert effects_sorted[1].aa_change == "PheTyr->Tyr"


def test_chr7_31609423_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="7:31609423",
        variant="sub(G->C)",
    )

    assert len(effects) == 4
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "CCDC129"
    assert effects_sorted[0].transcript_id == "NM_001257967_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "missense"
    assert effects_sorted[0].prot_pos == 113
    assert effects_sorted[0].prot_length == 1054
    assert effects_sorted[0].aa_change == "Arg->Thr"

    assert effects_sorted[1].gene == "CCDC129"
    assert effects_sorted[1].transcript_id == "NM_001257968_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "missense"
    assert effects_sorted[1].prot_pos == 129
    assert effects_sorted[1].prot_length == 1062
    assert effects_sorted[1].aa_change == "Arg->Thr"

    assert effects_sorted[2].gene == "CCDC129"
    assert effects_sorted[2].transcript_id == "NM_194300_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "missense"
    assert effects_sorted[2].prot_pos == 103
    assert effects_sorted[2].prot_length == 1044
    assert effects_sorted[2].aa_change == "Arg->Thr"

    assert effects_sorted[3].gene == "CCDC129"
    assert effects_sorted[3].transcript_id == "NR_047565_1"
    assert effects_sorted[3].strand == "+"
    assert effects_sorted[3].effect == "non-coding"
    assert effects_sorted[3].prot_pos is None
    assert effects_sorted[3].prot_length is None
    assert effects_sorted[3].aa_change is None


def test_chr3_136057284_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="3:136057284",
        variant="ins(TGA)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "STAG1"
    assert effect.transcript_id == "NM_005862_1"
    assert effect.strand == "-"
    assert effect.effect == "no-frame-shift"
    assert effect.prot_pos == 1227
    assert effect.prot_length == 1258
    assert effect.aa_change == "->Ser"


def test_chr1_120311364_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:120311364",
        variant="sub(C->A)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "HMGCS2"
    assert effects_sorted[0].transcript_id == "NM_001166107_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "missense"
    assert effects_sorted[0].prot_pos == 35
    assert effects_sorted[0].prot_length == 466
    assert effects_sorted[0].aa_change == "Arg->Met"

    assert effects_sorted[1].gene == "HMGCS2"
    assert effects_sorted[1].transcript_id == "NM_005518_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "missense"
    assert effects_sorted[1].prot_pos == 35
    assert effects_sorted[1].prot_length == 508
    assert effects_sorted[1].aa_change == "Arg->Met"


def test_chr3_128969525_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="3:128969525",
        variant="sub(G->T)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "COPG1"
    assert effect.transcript_id == "NM_016128_1"
    assert effect.strand == "+"
    assert effect.effect == "missense"
    assert effect.prot_pos == 13
    assert effect.prot_length == 874
    assert effect.aa_change == "Gly->Val"


def test_chr8_3046533_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="8:3046533",
        variant="sub(A->T)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "CSMD1"
    assert effect.transcript_id == "NM_033225_1"
    assert effect.strand == "-"
    assert effect.effect == "missense"
    assert effect.prot_pos == 1800
    assert effect.prot_length == 3564
    assert effect.aa_change == "Val->Glu"


def test_chr4_41748269_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    var = "ins(GCCGCGGCCGCTGCGGCT)"
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="4:41748269", variant=var,
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "PHOX2B"
    assert effect.transcript_id == "NM_003924_1"
    assert effect.strand == "-"
    assert effect.effect == "no-frame-shift"
    assert effect.prot_pos == 167
    assert effect.prot_length == 314
    assert effect.aa_change == "Ala->AlaAlaAlaAlaAlaAlaAla"


def test_chr9_130422308_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="9:130422308",
        variant="del(1)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "STXBP1"
    assert effects_sorted[0].transcript_id == "NM_001032221_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "splice-site"
    assert effects_sorted[0].prot_pos == 83
    assert effects_sorted[0].prot_length == 594
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 4
    assert effects_sorted[0].how_many_introns == 18
    assert effects_sorted[0].dist_from_coding == 0
    assert effects_sorted[0].dist_from_acceptor == 0
    assert effects_sorted[0].dist_from_donor == 1577
    assert effects_sorted[0].intron_length == 1578

    assert effects_sorted[1].gene == "STXBP1"
    assert effects_sorted[1].transcript_id == "NM_003165_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "splice-site"
    assert effects_sorted[1].prot_pos == 83
    assert effects_sorted[1].prot_length == 603
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].which_intron == 4
    assert effects_sorted[1].how_many_introns == 19
    assert effects_sorted[1].dist_from_coding == 0
    assert effects_sorted[1].dist_from_acceptor == 0
    assert effects_sorted[1].dist_from_donor == 1577
    assert effects_sorted[1].intron_length == 1578


def test_chr1_245019922_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:245019922",
        variant="del(10)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "HNRNPU"
    assert effects_sorted[0].transcript_id == "NM_004501_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "splice-site"
    assert effects_sorted[0].prot_pos == 563
    assert effects_sorted[0].prot_length == 806
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[1].which_intron == 9
    assert effects_sorted[1].how_many_introns == 13
    assert effects_sorted[1].dist_from_coding == -6
    assert effects_sorted[1].dist_from_acceptor == -6
    assert effects_sorted[1].dist_from_donor == 98
    assert effects_sorted[1].intron_length == 102

    assert effects_sorted[1].gene == "HNRNPU"
    assert effects_sorted[1].transcript_id == "NM_031844_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "splice-site"
    assert effects_sorted[1].prot_pos == 582
    assert effects_sorted[1].prot_length == 825
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].which_intron == 9
    assert effects_sorted[1].how_many_introns == 13
    assert effects_sorted[1].dist_from_coding == -6
    assert effects_sorted[1].dist_from_acceptor == -6
    assert effects_sorted[1].dist_from_donor == 98
    assert effects_sorted[1].intron_length == 102


def test_chr9_140509156_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="9:140509156",
        variant="ins(AGGAGG)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "ARRDC1"
    assert effect.transcript_id == "NM_152285_1"
    assert effect.strand == "+"
    assert effect.effect == "no-frame-shift"
    assert effect.prot_pos == 314
    assert effect.prot_length == 433
    assert effect.aa_change == "Gln->GlnGluGlu"


def test_chr20_57466823_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    # pylint: disable=too-many-statements
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="20:57466823",
        variant="sub(C->T)",
    )

    assert len(effects) == 8
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "GNAS"
    assert effects_sorted[0].transcript_id == "NM_000516_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "synonymous"
    assert effects_sorted[0].prot_pos == 14
    assert effects_sorted[0].prot_length == 394
    assert effects_sorted[0].aa_change == "Asn->Asn"

    assert effects_sorted[1].gene == "GNAS"
    assert effects_sorted[1].transcript_id == "NM_001077488_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "synonymous"
    assert effects_sorted[1].prot_pos == 14
    assert effects_sorted[1].prot_length == 395
    assert effects_sorted[1].aa_change == "Asn->Asn"

    assert effects_sorted[2].gene == "GNAS"
    assert effects_sorted[2].transcript_id == "NM_001077489_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "synonymous"
    assert effects_sorted[2].prot_pos == 14
    assert effects_sorted[2].prot_length == 379
    assert effects_sorted[2].aa_change == "Asn->Asn"

    assert effects_sorted[3].gene == "GNAS"
    assert effects_sorted[3].transcript_id == "NM_001077490_1"
    assert effects_sorted[3].strand == "+"
    assert effects_sorted[3].effect == "3'UTR-intron"
    assert effects_sorted[3].prot_pos is None
    assert effects_sorted[3].prot_length == 626
    assert effects_sorted[3].aa_change is None

    assert effects_sorted[4].gene == "GNAS"
    assert effects_sorted[4].transcript_id == "NM_016592_1"
    assert effects_sorted[4].strand == "+"
    assert effects_sorted[4].effect == "3'UTR-intron"
    assert effects_sorted[4].prot_pos is None
    assert effects_sorted[4].prot_length == 245
    assert effects_sorted[4].aa_change is None

    assert effects_sorted[5].gene == "GNAS"
    assert effects_sorted[5].transcript_id == "NM_080425_1"
    assert effects_sorted[5].strand == "+"
    assert effects_sorted[5].effect == "intron"
    assert effects_sorted[5].prot_pos == 690
    assert effects_sorted[5].prot_length == 1037
    assert effects_sorted[5].aa_change is None
    assert effects_sorted[5].which_intron == 1
    assert effects_sorted[5].how_many_introns == 12
    assert effects_sorted[5].dist_from_coding == 3843
    assert effects_sorted[5].dist_from_acceptor == 3843
    assert effects_sorted[5].dist_from_donor == 36434
    assert effects_sorted[5].intron_length == 40278

    assert effects_sorted[6].gene == "GNAS"
    assert effects_sorted[6].transcript_id == "NM_080426_1"
    assert effects_sorted[6].strand == "+"
    assert effects_sorted[6].effect == "synonymous"
    assert effects_sorted[6].prot_pos == 14
    assert effects_sorted[6].prot_length == 380
    assert effects_sorted[6].aa_change == "Asn->Asn"

    assert effects_sorted[7].gene == "GNAS"
    assert effects_sorted[7].transcript_id == "NR_003259_1"
    assert effects_sorted[7].strand == "+"
    assert effects_sorted[7].effect == "non-coding-intron"
    assert effects_sorted[7].prot_pos is None
    assert effects_sorted[7].prot_length is None
    assert effects_sorted[7].aa_change is None


def test_chr1_156354348_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:156354348",
        variant="del(1)",
    )

    assert len(effects) == 4
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "RHBG"
    assert effects_sorted[0].transcript_id == "NM_001256395_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "splice-site"
    assert effects_sorted[0].prot_pos == 353
    assert effects_sorted[0].prot_length == 389
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 10
    assert effects_sorted[0].how_many_introns == 11
    assert effects_sorted[0].dist_from_coding == 0
    assert effects_sorted[0].dist_from_acceptor == 0
    assert effects_sorted[0].dist_from_donor == 0
    assert effects_sorted[0].intron_length == 1

    assert effects_sorted[1].gene == "RHBG"
    assert effects_sorted[1].transcript_id == "NM_001256396_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "splice-site"
    assert effects_sorted[1].prot_pos == 392
    assert effects_sorted[1].prot_length == 428
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].which_intron == 10
    assert effects_sorted[1].how_many_introns == 11
    assert effects_sorted[1].dist_from_coding == 0
    assert effects_sorted[1].dist_from_acceptor == 0
    assert effects_sorted[1].dist_from_donor == 0
    assert effects_sorted[1].intron_length == 1

    assert effects_sorted[2].gene == "RHBG"
    assert effects_sorted[2].transcript_id == "NM_020407_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "splice-site"
    assert effects_sorted[2].prot_pos == 422
    assert effects_sorted[2].prot_length == 458
    assert effects_sorted[2].aa_change is None
    assert effects_sorted[2].which_intron == 9
    assert effects_sorted[2].how_many_introns == 10
    assert effects_sorted[2].dist_from_coding == 0
    assert effects_sorted[2].dist_from_acceptor == 0
    assert effects_sorted[2].dist_from_donor == 0
    assert effects_sorted[2].intron_length == 1

    assert effects_sorted[3].gene == "RHBG"
    assert effects_sorted[3].transcript_id == "NR_046115_1"
    assert effects_sorted[3].strand == "+"
    assert effects_sorted[3].effect == "non-coding"
    assert effects_sorted[3].prot_pos is None
    assert effects_sorted[3].prot_length is None
    assert effects_sorted[3].aa_change is None


def test_chr17_76528711_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="17:76528711",
        variant="sub(C->T)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "DNAH17"
    assert effect.transcript_id == "NM_173628_1"
    assert effect.strand == "-"
    assert effect.effect == "synonymous"
    assert effect.prot_pos == 989
    assert effect.prot_length == 4462
    assert effect.aa_change == "Arg->Arg"


def test_chr1_244816618_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:244816618",
        variant="ins(G)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "DESI2"
    assert effect.transcript_id == "NM_016076_1"
    assert effect.strand == "+"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 194
    assert effect.aa_change is None


def test_chr10_46248650_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="10:46248650",
        variant="del(3)",
    )

    assert len(effects) == 3
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "FAM21C"
    assert effects_sorted[0].transcript_id == "NM_001169106_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "no-frame-shift-newStop"
    assert effects_sorted[0].prot_pos == 382
    assert effects_sorted[0].prot_length == 1279
    assert effects_sorted[0].aa_change == "SerGln->End"

    assert effects_sorted[1].gene == "FAM21C"
    assert effects_sorted[1].transcript_id == "NM_001169107_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "no-frame-shift-newStop"
    assert effects_sorted[1].prot_pos == 358
    assert effects_sorted[1].prot_length == 1245
    assert effects_sorted[1].aa_change == "SerGln->End"

    assert effects_sorted[2].gene == "FAM21C"
    assert effects_sorted[2].transcript_id == "NM_015262_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "no-frame-shift-newStop"
    assert effects_sorted[2].prot_pos == 382
    assert effects_sorted[2].prot_length == 1320
    assert effects_sorted[2].aa_change == "SerGln->End"


def test_chr15_41864763_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="15:41864763",
        variant="del(3)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "TYRO3"
    assert effect.transcript_id == "NM_006293_1"
    assert effect.strand == "+"
    assert effect.effect == "splice-site"
    assert effect.prot_pos == 626
    assert effect.prot_length == 890
    assert effect.aa_change is None
    assert effect.which_intron == 15
    assert effect.how_many_introns == 18
    assert effect.dist_from_coding == 0
    assert effect.dist_from_acceptor == 434
    assert effect.dist_from_donor == 0
    assert effect.intron_length == 437


def test_chr3_131100722_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="3:131100722",
        variant="sub(C->G)",
    )

    assert len(effects) == 4
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "NUDT16"
    assert effects_sorted[0].transcript_id == "NM_001171905_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "5'UTR-intron"
    assert effects_sorted[0].prot_pos is None
    assert effects_sorted[0].prot_length == 159
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "NUDT16"
    assert effects_sorted[1].transcript_id == "NM_001171906_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "missense"
    assert effects_sorted[1].prot_pos == 25
    assert effects_sorted[1].prot_length == 227
    assert effects_sorted[1].aa_change == "Ala->Gly"

    assert effects_sorted[2].gene == "NUDT16"
    assert effects_sorted[2].transcript_id == "NM_152395_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "missense"
    assert effects_sorted[2].prot_pos == 25
    assert effects_sorted[2].prot_length == 195
    assert effects_sorted[2].aa_change == "Ala->Gly"

    assert effects_sorted[3].gene == "NUDT16"
    assert effects_sorted[3].transcript_id == "NR_033268_1"
    assert effects_sorted[3].strand == "+"
    assert effects_sorted[3].effect == "non-coding"
    assert effects_sorted[3].prot_pos is None
    assert effects_sorted[3].prot_length is None
    assert effects_sorted[3].aa_change is None


def test_chr1_42619122_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:42619122",
        variant="sub(A->G)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "GUCA2B"
    assert effect.transcript_id == "NM_007102_1"
    assert effect.strand == "+"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 112
    assert effect.aa_change is None


def test_chr1_16558543_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:16558543",
        variant="sub(T->C)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "RSG1"
    assert effect.transcript_id == "NM_030907_1"
    assert effect.strand == "-"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 259
    assert effect.prot_length == 258
    assert effect.aa_change is None


def test_chr1_47515176_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:47515176",
        variant="ins(TAGAAATATAAT)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "CYP4X1"
    assert effect.transcript_id == "NM_178033_1"
    assert effect.strand == "+"
    assert effect.effect == "no-frame-shift-newStop"
    assert effect.prot_pos == 452
    assert effect.prot_length == 509
    assert effect.aa_change == "Arg->IleGluIleEndTrp"


def test_chr1_120934555_sub_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:120934555",
        variant="sub(C->T)",
    )

    assert len(effects) == 4
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "FCGR1B"
    assert effects_sorted[0].transcript_id == "NM_001004340_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "intron"
    assert effects_sorted[0].prot_pos == 11
    assert effects_sorted[0].prot_length == 188
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 1
    assert effects_sorted[0].how_many_introns == 2
    assert effects_sorted[0].dist_from_coding == 1308
    assert effects_sorted[0].dist_from_acceptor == 4261
    assert effects_sorted[0].dist_from_donor == 1308
    assert effects_sorted[0].intron_length == 5570

    assert effects_sorted[1].gene == "FCGR1B"
    assert effects_sorted[1].transcript_id == "NM_001017986_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "missense"
    assert effects_sorted[1].prot_pos == 45
    assert effects_sorted[1].prot_length == 280
    assert effects_sorted[1].aa_change == "Val->Met"

    assert effects_sorted[2].gene == "FCGR1B"
    assert effects_sorted[2].transcript_id == "NM_001244910_1"
    assert effects_sorted[2].strand == "-"
    assert effects_sorted[2].effect == "missense"
    assert effects_sorted[2].prot_pos == 45
    assert effects_sorted[2].prot_length == 224
    assert effects_sorted[2].aa_change == "Val->Met"

    assert effects_sorted[3].gene == "FCGR1B"
    assert effects_sorted[3].transcript_id == "NR_045213_1"
    assert effects_sorted[3].strand == "-"
    assert effects_sorted[3].effect == "non-coding"
    assert effects_sorted[3].prot_pos is None
    assert effects_sorted[3].prot_length is None
    assert effects_sorted[3].aa_change is None


def test_chr1_26190329_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="1:26190329", variant="del(6)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "PAQR7"
    assert effect.transcript_id == "NM_178422_1"
    assert effect.strand == "-"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 346
    assert effect.aa_change is None


def test_chr1_42628578_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="1:42628578", variant="del(1)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "GUCA2A"
    assert effect.transcript_id == "NM_033553_1"
    assert effect.strand == "-"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 116
    assert effect.prot_length == 115
    assert effect.aa_change is None


def test_chr1_203652334_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:203652334",
        variant="del(6)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "ATP2B4"
    assert effects_sorted[0].transcript_id == "NM_001001396_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "noStart"
    assert effects_sorted[0].prot_pos == 1
    assert effects_sorted[0].prot_length == 1170
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "ATP2B4"
    assert effects_sorted[1].transcript_id == "NM_001684_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "noStart"
    assert effects_sorted[1].prot_pos == 1
    assert effects_sorted[1].prot_length == 1205
    assert effects_sorted[1].aa_change is None


def test_chr2_133426005_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="2:133426005",
        variant="del(2)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "LYPD1"
    assert effects_sorted[0].transcript_id == "NM_001077427_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "noStart"
    assert effects_sorted[0].prot_pos == 1
    assert effects_sorted[0].prot_length == 89
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "LYPD1"
    assert effects_sorted[1].transcript_id == "NM_144586_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "frame-shift"
    assert effects_sorted[1].prot_pos == 53
    assert effects_sorted[1].prot_length == 141


def test_chr1_237060943_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:237060943",
        variant="ins(TTTGGAATAG)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "MTR"
    assert effect.transcript_id == "NM_000254_1"
    assert effect.strand == "+"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 1266
    assert effect.prot_length == 1265
    assert effect.aa_change is None


def test_chr1_160854666_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:160854666",
        variant="ins(AA)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "ITLN1"
    assert effect.transcript_id == "NM_017625_1"
    assert effect.strand == "-"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 313
    assert effect.aa_change is None


def test_chr1_248903150_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    var = "ins(AGTCTAGGCAATCTTCCCAGAATGGAAACCCAATCCACTCTTACTA)"
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="1:248903150", variant=var,
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "LYPD8"
    assert effect.transcript_id == "NM_001085474_1"
    assert effect.strand == "-"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 79
    assert effect.aa_change is None


def test_chr2_58390000_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="2:58390000", variant="del(1)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "FANCL"
    assert effects_sorted[0].transcript_id == "NM_001114636_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "splice-site"
    assert effects_sorted[0].prot_pos == 307
    assert effects_sorted[0].prot_length == 380
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 11
    assert effects_sorted[0].how_many_introns == 13
    assert effects_sorted[0].dist_from_coding == 0
    assert effects_sorted[0].dist_from_acceptor == 1226
    assert effects_sorted[0].dist_from_donor == 0
    assert effects_sorted[0].intron_length == 1227

    assert effects_sorted[1].gene == "FANCL"
    assert effects_sorted[1].transcript_id == "NM_018062_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "splice-site"
    assert effects_sorted[1].prot_pos == 302
    assert effects_sorted[1].prot_length == 375
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].which_intron == 11
    assert effects_sorted[1].how_many_introns == 13
    assert effects_sorted[1].dist_from_coding == 0
    assert effects_sorted[1].dist_from_acceptor == 1226
    assert effects_sorted[1].dist_from_donor == 0
    assert effects_sorted[1].intron_length == 1227


def test_chr20_5295014_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="20:5295014",
        variant="ins(AAG)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "PROKR2"
    assert effect.transcript_id == "NM_144773_1"
    assert effect.strand == "-"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 384
    assert effect.aa_change is None


def test_chr5_126859172_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="5:126859172",
        variant="del(3)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "PRRC1"
    assert effect.transcript_id == "NM_130809_1"
    assert effect.strand == "+"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 445
    assert effect.aa_change is None


def test_chr4_141471529_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="4:141471529",
        variant="ins(T)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "ELMOD2"
    assert effect.transcript_id == "NM_153702_1"
    assert effect.strand == "+"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 294
    assert effect.prot_length == 293
    assert effect.aa_change is None


def test_chr1_33330213_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="1:33330213", variant="del(1)",
    )

    assert len(effects) == 3
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "FNDC5"
    assert effects_sorted[0].transcript_id == "NM_001171940_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "intron"
    assert effects_sorted[0].prot_pos == 178
    assert effects_sorted[0].prot_length == 181
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 5
    assert effects_sorted[0].how_many_introns == 5
    assert effects_sorted[0].dist_from_coding == 153
    assert effects_sorted[0].dist_from_acceptor == 859
    assert effects_sorted[0].dist_from_donor == 153
    assert effects_sorted[0].intron_length == 1013

    assert effects_sorted[1].gene == "FNDC5"
    assert effects_sorted[1].transcript_id == "NM_001171941_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "noEnd"
    assert effects_sorted[1].prot_pos == 154
    assert effects_sorted[1].prot_length == 153
    assert effects_sorted[1].aa_change is None

    assert effects_sorted[2].gene == "FNDC5"
    assert effects_sorted[2].transcript_id == "NM_153756_1"
    assert effects_sorted[2].strand == "-"
    assert effects_sorted[2].effect == "intron"
    assert effects_sorted[2].prot_pos == 212
    assert effects_sorted[2].prot_length == 212
    assert effects_sorted[2].aa_change is None
    assert effects_sorted[2].which_intron == 5
    assert effects_sorted[2].how_many_introns == 5
    assert effects_sorted[2].dist_from_coding == 51
    assert effects_sorted[2].dist_from_acceptor == 312
    assert effects_sorted[2].dist_from_donor == 51
    assert effects_sorted[2].intron_length == 364


def test_chr5_96430453_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="5:96430453",
        variant="ins(TAG)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "LIX1"
    assert effect.transcript_id == "NM_153234_1"
    assert effect.strand == "-"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 283
    assert effect.prot_length == 282
    assert effect.aa_change is None


def test_chr10_25138774_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    var = "ins(ATATTGGATTTAATCCAAGTTAACAAAAATAAAGCCGCAGGA)"
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="10:25138774", variant=var,
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "PRTFDC1"
    assert effect.transcript_id == "NM_020200_1"
    assert effect.strand == "-"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 226
    assert effect.prot_length == 225
    assert effect.aa_change is None


def test_chr2_218747134_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="2:218747134",
        variant="ins(AGTTAT)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "TNS1"
    assert effect.transcript_id == "NM_022648_1"
    assert effect.strand == "-"
    assert effect.effect == "no-frame-shift-newStop"
    assert effect.prot_pos == 291
    assert effect.prot_length == 1735
    assert effect.aa_change == "Asp->GluEndLeu"


def test_chr11_3846347_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    # pylint: disable=too-many-statements
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="11:3846347",
        variant="del(12)",
    )

    assert len(effects) == 16
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "PGAP2"
    assert effects_sorted[0].transcript_id == "NM_001145438_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "no-frame-shift"
    assert effects_sorted[0].prot_pos == 261
    assert effects_sorted[0].prot_length == 307
    assert effects_sorted[0].aa_change == "CysGluAlaGlyVal->Leu"

    assert effects_sorted[1].gene == "PGAP2"
    assert effects_sorted[1].transcript_id == "NM_001256235_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "no-frame-shift"
    assert effects_sorted[1].prot_pos == 226
    assert effects_sorted[1].prot_length == 272
    assert effects_sorted[1].aa_change == "CysGluAlaGlyVal->Leu"

    assert effects_sorted[2].gene == "PGAP2"
    assert effects_sorted[2].transcript_id == "NM_001256236_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "no-frame-shift"
    assert effects_sorted[2].prot_pos == 326
    assert effects_sorted[2].prot_length == 372
    assert effects_sorted[2].aa_change == "CysGluAlaGlyVal->Leu"

    assert effects_sorted[3].gene == "PGAP2"
    assert effects_sorted[3].transcript_id == "NM_001256237_1"
    assert effects_sorted[3].strand == "+"
    assert effects_sorted[3].effect == "noEnd"
    assert effects_sorted[3].prot_pos == 291
    assert effects_sorted[3].prot_length == 291
    assert effects_sorted[3].aa_change is None

    assert effects_sorted[4].gene == "PGAP2"
    assert effects_sorted[4].transcript_id == "NM_001256238_1"
    assert effects_sorted[4].strand == "+"
    assert effects_sorted[4].effect == "noEnd"
    assert effects_sorted[4].prot_pos == 232
    assert effects_sorted[4].prot_length == 232
    assert effects_sorted[4].aa_change is None

    assert effects_sorted[5].gene == "PGAP2"
    assert effects_sorted[5].transcript_id == "NM_001256239_1"
    assert effects_sorted[5].strand == "+"
    assert effects_sorted[5].effect == "no-frame-shift"
    assert effects_sorted[5].prot_pos == 204
    assert effects_sorted[5].prot_length == 250
    assert effects_sorted[5].aa_change == "CysGluAlaGlyVal->Leu"

    assert effects_sorted[6].gene == "PGAP2"
    assert effects_sorted[6].transcript_id == "NM_001256240_1"
    assert effects_sorted[6].strand == "+"
    assert effects_sorted[6].effect == "no-frame-shift"
    assert effects_sorted[6].prot_pos == 208
    assert effects_sorted[6].prot_length == 254
    assert effects_sorted[6].aa_change == "CysGluAlaGlyVal->Leu"

    assert effects_sorted[7].gene == "PGAP2"
    assert effects_sorted[7].transcript_id == "NM_014489_1"
    assert effects_sorted[7].strand == "+"
    assert effects_sorted[7].effect == "no-frame-shift"
    assert effects_sorted[7].prot_pos == 269
    assert effects_sorted[7].prot_length == 315
    assert effects_sorted[7].aa_change == "CysGluAlaGlyVal->Leu"

    assert effects_sorted[8].gene == "PGAP2"
    assert effects_sorted[8].transcript_id == "NR_027016_1"
    assert effects_sorted[8].strand == "+"
    assert effects_sorted[8].effect == "non-coding"
    assert effects_sorted[8].prot_pos is None
    assert effects_sorted[8].prot_length is None
    assert effects_sorted[8].aa_change is None

    assert effects_sorted[9].gene == "PGAP2"
    assert effects_sorted[9].transcript_id == "NR_027017_1"
    assert effects_sorted[9].strand == "+"
    assert effects_sorted[9].effect == "non-coding"
    assert effects_sorted[9].prot_pos is None
    assert effects_sorted[9].prot_length is None
    assert effects_sorted[9].aa_change is None

    assert effects_sorted[10].gene == "PGAP2"
    assert effects_sorted[10].transcript_id == "NR_027018_1"
    assert effects_sorted[10].strand == "+"
    assert effects_sorted[10].effect == "non-coding"
    assert effects_sorted[10].prot_pos is None
    assert effects_sorted[10].prot_length is None
    assert effects_sorted[10].aa_change is None

    assert effects_sorted[11].gene == "PGAP2"
    assert effects_sorted[11].transcript_id == "NR_045923_1"
    assert effects_sorted[11].strand == "+"
    assert effects_sorted[11].effect == "non-coding"
    assert effects_sorted[11].prot_pos is None
    assert effects_sorted[11].prot_length is None
    assert effects_sorted[11].aa_change is None

    assert effects_sorted[12].gene == "PGAP2"
    assert effects_sorted[12].transcript_id == "NR_045925_1"
    assert effects_sorted[12].strand == "+"
    assert effects_sorted[12].effect == "non-coding"
    assert effects_sorted[12].prot_pos is None
    assert effects_sorted[12].prot_length is None
    assert effects_sorted[12].aa_change is None

    assert effects_sorted[13].gene == "PGAP2"
    assert effects_sorted[13].transcript_id == "NR_045926_1"
    assert effects_sorted[13].strand == "+"
    assert effects_sorted[13].effect == "non-coding"
    assert effects_sorted[13].prot_pos is None
    assert effects_sorted[13].prot_length is None
    assert effects_sorted[13].aa_change is None

    assert effects_sorted[14].gene == "PGAP2"
    assert effects_sorted[14].transcript_id == "NR_045927_1"
    assert effects_sorted[14].strand == "+"
    assert effects_sorted[14].effect == "non-coding"
    assert effects_sorted[14].prot_pos is None
    assert effects_sorted[14].prot_length is None
    assert effects_sorted[14].aa_change is None

    assert effects_sorted[15].gene == "PGAP2"
    assert effects_sorted[15].transcript_id == "NR_045929_1"
    assert effects_sorted[15].strand == "+"
    assert effects_sorted[15].effect == "non-coding"
    assert effects_sorted[15].prot_pos is None
    assert effects_sorted[15].prot_length is None
    assert effects_sorted[15].aa_change is None


def test_chr1_145567756_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:145567756",
        variant="ins(CTC)",
    )

    assert len(effects) == 4
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "NBPF10"
    assert effects_sorted[0].transcript_id == "NM_001039703_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "intron"
    assert effects_sorted[0].prot_pos == 2872
    assert effects_sorted[0].prot_length == 3626
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 68
    assert effects_sorted[0].how_many_introns == 85
    assert effects_sorted[0].dist_from_coding == 202296
    assert effects_sorted[0].dist_from_acceptor == 853155
    assert effects_sorted[0].dist_from_donor == 202296
    assert effects_sorted[0].intron_length == 1055451

    assert effects_sorted[1].gene == "LOC100288142"
    assert effects_sorted[1].transcript_id == "NM_001278267_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "intron"
    assert effects_sorted[1].prot_pos == 3663
    assert effects_sorted[1].prot_length == 4963
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].which_intron == 99
    assert effects_sorted[1].how_many_introns == 130
    assert effects_sorted[1].dist_from_coding == 203081
    assert effects_sorted[1].dist_from_acceptor == 852263
    assert effects_sorted[1].dist_from_donor == 203081
    assert effects_sorted[1].intron_length == 1055344

    assert effects_sorted[2].gene == "ANKRD35"
    assert effects_sorted[2].transcript_id == "NM_001280799_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "noEnd"
    assert effects_sorted[2].prot_pos == 912
    assert effects_sorted[2].prot_length == 911
    assert effects_sorted[2].aa_change is None

    assert effects_sorted[3].gene == "ANKRD35"
    assert effects_sorted[3].transcript_id == "NM_144698_1"
    assert effects_sorted[3].strand == "+"
    assert effects_sorted[3].effect == "noEnd"
    assert effects_sorted[3].prot_pos == 1002
    assert effects_sorted[3].prot_length == 1001
    assert effects_sorted[3].aa_change is None


def test_chr3_135969219_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    var = "ins(TGGCGGCGGCATTACGGG)"
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="3:135969219", variant=var,
    )

    assert len(effects) == 2
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "PCCB"
    assert effects_sorted[0].transcript_id == "NM_000532_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "noStart"
    assert effects_sorted[0].prot_pos == 1
    assert effects_sorted[0].prot_length == 539
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "PCCB"
    assert effects_sorted[1].transcript_id == "NM_001178014_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "noStart"
    assert effects_sorted[1].prot_pos == 1
    assert effects_sorted[1].prot_length == 559
    assert effects_sorted[1].aa_change is None


def test_chr1_27180332_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="1:27180332", variant="del(1)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "ZDHHC18"
    assert effect.transcript_id == "NM_032283_1"
    assert effect.strand == "+"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 389
    assert effect.prot_length == 388
    assert effect.aa_change is None


def test_chr1_1425787_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    var = "ins(ACGTGACATTTAGCTGTCACTTCTGGTGGGCTCCTGCCA)"
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="1:1425787", variant=var,
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "ATAD3B"
    assert effect.transcript_id == "NM_031921_1"
    assert effect.strand == "+"
    assert effect.effect == "no-frame-shift-newStop"
    assert effect.prot_pos == 496
    assert effect.prot_length == 648
    assert (
        effect.aa_change
        == "Pro->ProArgAspIleEndLeuSerLeuLeuValGlySerCysGln"
    )


def test_chr1_33476432_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    var = "ins(AGGATGTGGCTTTGGAGA)"
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="1:33476432", variant=var,
    )

    assert len(effects) == 3

    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "AK2"
    assert effects_sorted[0].transcript_id == "NM_001199199_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "noEnd"
    assert effects_sorted[0].prot_pos == 225
    assert effects_sorted[0].prot_length == 224
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "AK2"
    assert effects_sorted[1].transcript_id == "NM_013411_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "noEnd"
    assert effects_sorted[1].prot_pos == 233
    assert effects_sorted[1].prot_length == 232
    assert effects_sorted[1].aa_change is None

    assert effects_sorted[2].gene == "AK2"
    assert effects_sorted[2].transcript_id == "NR_037591_1"
    assert effects_sorted[2].strand == "-"
    assert effects_sorted[2].effect == "non-coding"
    assert effects_sorted[2].prot_pos is None
    assert effects_sorted[2].prot_length is None
    assert effects_sorted[2].aa_change is None


def test_chr1_245017754_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:245017754",
        variant="del(3)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "HNRNPU"
    assert effects_sorted[0].transcript_id == "NM_004501_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "noEnd"
    assert effects_sorted[0].prot_pos == 806
    assert effects_sorted[0].prot_length == 806
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "HNRNPU"
    assert effects_sorted[1].transcript_id == "NM_031844_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "noEnd"
    assert effects_sorted[1].prot_pos == 825
    assert effects_sorted[1].prot_length == 825
    assert effects_sorted[1].aa_change is None


def test_chr4_26862842_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="4:26862842", variant="del(3)",
    )

    assert len(effects) == 3
    effects_sorted = sorted(
        effects, key=lambda k: k.transcript_id)  # type: ignore

    assert effects_sorted[0].gene == "STIM2"
    assert effects_sorted[0].transcript_id == "NM_001169117_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "noStart"
    assert effects_sorted[0].prot_pos == 1
    assert effects_sorted[0].prot_length == 599
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "STIM2"
    assert effects_sorted[1].transcript_id == "NM_001169118_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "noStart"
    assert effects_sorted[1].prot_pos == 1
    assert effects_sorted[1].prot_length == 754
    assert effects_sorted[1].aa_change is None

    assert effects_sorted[2].gene == "STIM2"
    assert effects_sorted[2].transcript_id == "NM_020860_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "noStart"
    assert effects_sorted[2].prot_pos == 1
    assert effects_sorted[2].prot_length == 746
    assert effects_sorted[2].aa_change is None


def test_chr5_68578558_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="5:68578558",
        variant="ins(TA)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "CCDC125"
    assert effect.transcript_id == "NM_176816_1"
    assert effect.strand == "-"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 512
    assert effect.prot_length == 511
    assert effect.aa_change is None


def test_chr6_33054014_ins_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="6:33054014", variant="ins(C)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "HLA-DPB1"
    assert effect.transcript_id == "NM_002121_6"
    assert effect.strand == "+"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 259
    assert effect.prot_length == 258
    assert effect.aa_change is None


def test_chr1_152648485_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genome_2013,
        location="1:152648485",
        variant="del(13)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "LCE2C"
    assert effect.transcript_id == "NM_178429_1"
    assert effect.strand == "+"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 110
    assert effect.aa_change is None


def test_chr1_7844919_del_var(
    genome_2013: ReferenceGenome, gene_models_2013: GeneModels,
) -> None:
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genome_2013,
        location="1:7844919", variant="del(21)",
    )
    assert len(effects) == 1
    effect = effects[0]

    assert effect.gene == "PER3"
    assert effect.transcript_id == "NM_016831_1"
    assert effect.strand == "+"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 1201
    assert effect.aa_change is None
