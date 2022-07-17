# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest
from dae.effect_annotation.annotator import EffectAnnotator
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.reference_genome import \
    build_reference_genome_from_resource
from dae.genomic_resources.gene_models import \
    load_gene_models_from_resource


@pytest.fixture(scope="module")
def grr_repository():
    return build_genomic_resource_repository()


@pytest.fixture(scope="module")
def genomic_sequence_2013(grr_repository):
    resource = grr_repository.get_resource(
        "hg19/genomes/GATK_ResourceBundle_5777_b37_phiX174")
    return build_reference_genome_from_resource(resource).open()


@pytest.fixture(scope="module")
def gene_models_2013(grr_repository):
    resource = grr_repository.get_resource(
        "hg19/gene_models/refGene_v201309")
    return load_gene_models_from_resource(resource)


def test_chr12_130827138_del_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="12:130827138",
        var="del(4)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "PIWIL1"
    assert effects_sorted[0].transcript_id == "NM_001190971_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "noStart"
    assert effects_sorted[0].prot_pos == 1
    assert effects_sorted[0].prot_length == 829
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "PIWIL1"
    assert effects_sorted[1].transcript_id == "NM_004764_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "noStart"
    assert effects_sorted[1].prot_pos == 1
    assert effects_sorted[1].prot_length == 861
    assert effects_sorted[1].aa_change is None


def test_chr12_64841908_del_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="12:64841908",
        var="del(2)",
    )

    assert effect.gene == "XPOT"
    assert effect.transcript_id == "NM_007235_1"
    assert effect.strand == "+"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 962
    assert effect.prot_length == 962
    assert effect.aa_change is None


def test_chr1_95712170_del_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="1:95712170", var="del(3)"
    )

    assert len(effects) == 7
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "RWDD3"
    assert effects_sorted[0].transcript_id == "NM_001128142_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "3'UTR-intron"
    assert effects_sorted[0].prot_pos is None
    assert effects_sorted[0].prot_length == 195
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "RWDD3"
    assert effects_sorted[1].transcript_id == "NM_001199682_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "noEnd"
    assert effects_sorted[1].prot_pos == 200
    assert effects_sorted[1].prot_length == 200
    assert effects_sorted[1].aa_change is None

    assert effects_sorted[2].gene == "RWDD3"
    assert effects_sorted[2].transcript_id == "NM_001278247_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "noEnd"
    assert effects_sorted[2].prot_pos == 185
    assert effects_sorted[2].prot_length == 185
    assert effects_sorted[2].aa_change is None

    assert effects_sorted[3].gene == "RWDD3"
    assert effects_sorted[3].transcript_id == "NM_001278248_1"
    assert effects_sorted[3].strand == "+"
    assert effects_sorted[3].effect == "no-frame-shift"
    assert effects_sorted[3].prot_pos == 201
    assert effects_sorted[3].prot_length == 252
    assert effects_sorted[3].aa_change == "Ile->"

    assert effects_sorted[4].gene == "RWDD3"
    assert effects_sorted[4].transcript_id == "NM_015485_1"
    assert effects_sorted[4].strand == "+"
    assert effects_sorted[4].effect == "no-frame-shift"
    assert effects_sorted[4].prot_pos == 216
    assert effects_sorted[4].prot_length == 267
    assert effects_sorted[4].aa_change == "Ile->"

    assert effects_sorted[5].gene == "RWDD3"
    assert effects_sorted[5].transcript_id == "NR_103483_1"
    assert effects_sorted[5].strand == "+"
    assert effects_sorted[5].effect == "non-coding"
    assert effects_sorted[5].prot_pos is None
    assert effects_sorted[5].prot_length is None
    assert effects_sorted[5].aa_change is None

    assert effects_sorted[6].gene == "RWDD3"
    assert effects_sorted[6].transcript_id == "NR_103484_1"
    assert effects_sorted[6].strand == "+"
    assert effects_sorted[6].effect == "non-coding"
    assert effects_sorted[6].prot_pos is None
    assert effects_sorted[6].prot_length is None
    assert effects_sorted[6].aa_change is None


def test_chr19_35249941_ins_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="19:35249941",
        var="ins(AA)",
    )

    assert effect.gene == "ZNF599"
    assert effect.transcript_id == "NM_001007248_1"
    assert effect.strand == "-"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 589
    assert effect.prot_length == 588
    assert effect.aa_change is None


def test_chr3_195966608_del_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="3:195966608",
        var="del(4)",
    )

    assert effect.gene == "PCYT1A"
    assert effect.transcript_id == "NM_005017_1"
    assert effect.strand == "-"
    assert effect.effect == "splice-site"
    assert effect.prot_pos == 237
    assert effect.prot_length == 367
    assert effect.aa_change is None
    assert effect.which_intron == 8
    assert effect.how_many_introns == 9
    assert effect.dist_from_coding == 1
    assert effect.dist_from_acceptor == 1
    assert effect.dist_from_donor == 2207
    assert effect.intron_length == 2212


def test_chr1_156786466_ins_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="1:156786466",
        var="ins(A)",
    )

    assert len(effects) == 5
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "NTRK1"
    assert effects_sorted[0].transcript_id == "NM_001007792_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "intron"
    assert effects_sorted[0].prot_pos == 4
    assert effects_sorted[0].prot_length == 760
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 1
    assert effects_sorted[0].how_many_introns == 16
    assert effects_sorted[0].dist_from_coding == 835
    assert effects_sorted[0].dist_from_acceptor == 25407
    assert effects_sorted[0].dist_from_donor == 835
    assert effects_sorted[0].intron_length == 26242

    assert effects_sorted[1].gene == "SH2D2A"
    assert effects_sorted[1].transcript_id == "NM_001161441_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "splice-site"
    assert effects_sorted[1].prot_pos == 12
    assert effects_sorted[1].prot_length == 399
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].which_intron == 1
    assert effects_sorted[1].how_many_introns == 8
    assert effects_sorted[1].dist_from_coding == 1
    assert effects_sorted[1].dist_from_acceptor == 579
    assert effects_sorted[1].dist_from_donor == 1
    assert effects_sorted[1].intron_length == 580

    assert effects_sorted[2].gene == "SH2D2A"
    assert effects_sorted[2].transcript_id == "NM_001161442_1"
    assert effects_sorted[2].strand == "-"
    assert effects_sorted[2].effect == "splice-site"
    assert effects_sorted[2].prot_pos == 4
    assert effects_sorted[2].prot_length == 371
    assert effects_sorted[2].aa_change is None
    assert effects_sorted[2].which_intron == 1
    assert effects_sorted[2].how_many_introns == 8
    assert effects_sorted[2].dist_from_coding == 1
    assert effects_sorted[2].dist_from_acceptor == 610
    assert effects_sorted[2].dist_from_donor == 1
    assert effects_sorted[2].intron_length == 611

    assert effects_sorted[3].gene == "SH2D2A"
    assert effects_sorted[3].transcript_id == "NM_001161444_1"
    assert effects_sorted[3].strand == "-"
    assert effects_sorted[3].effect == "splice-site"
    assert effects_sorted[3].prot_pos == 12
    assert effects_sorted[3].prot_length == 389
    assert effects_sorted[3].aa_change is None
    assert effects_sorted[3].which_intron == 1
    assert effects_sorted[3].how_many_introns == 7
    assert effects_sorted[3].dist_from_coding == 1
    assert effects_sorted[3].dist_from_acceptor == 579
    assert effects_sorted[3].dist_from_donor == 1
    assert effects_sorted[3].intron_length == 580

    assert effects_sorted[4].gene == "SH2D2A"
    assert effects_sorted[4].transcript_id == "NM_003975_1"
    assert effects_sorted[4].strand == "-"
    assert effects_sorted[4].effect == "splice-site"
    assert effects_sorted[4].prot_pos == 12
    assert effects_sorted[4].prot_length == 389
    assert effects_sorted[4].aa_change is None
    assert effects_sorted[4].which_intron == 1
    assert effects_sorted[4].how_many_introns == 8
    assert effects_sorted[4].dist_from_coding == 1
    assert effects_sorted[4].dist_from_acceptor == 579
    assert effects_sorted[4].dist_from_donor == 1
    assert effects_sorted[4].intron_length == 580


def test_chr1_21050866_del_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="1:21050866",
        var="del(34)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "SH2D5"
    assert effects_sorted[0].transcript_id == "NM_001103160_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "splice-site"
    assert effects_sorted[0].prot_pos == 127
    assert effects_sorted[0].prot_length == 339
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 5
    assert effects_sorted[0].how_many_introns == 8
    assert effects_sorted[0].dist_from_coding == -11
    assert effects_sorted[0].dist_from_acceptor == 121
    assert effects_sorted[0].dist_from_donor == -11
    assert effects_sorted[0].intron_length == 144

    assert effects_sorted[1].gene == "SH2D5"
    assert effects_sorted[1].transcript_id == "NM_001103161_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "splice-site"
    assert effects_sorted[1].prot_pos == 211
    assert effects_sorted[1].prot_length == 423
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].which_intron == 6
    assert effects_sorted[1].how_many_introns == 9
    assert effects_sorted[1].dist_from_coding == -11
    assert effects_sorted[1].dist_from_acceptor == 121
    assert effects_sorted[1].dist_from_donor == -11
    assert effects_sorted[1].intron_length == 144


def test_chr2_111753543_del_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="2:111753543",
        var="del(54)",
    )

    assert effect.gene == "ACOXL"
    assert effect.transcript_id == "NM_001142807_1"
    assert effect.strand == "+"
    assert effect.effect == "splice-site"
    assert effect.prot_pos == 428
    assert effect.prot_length == 580
    assert effect.aa_change is None
    assert effect.which_intron == 14
    assert effect.how_many_introns == 17
    assert effect.dist_from_coding == -39
    assert effect.dist_from_acceptor == 35607
    assert effect.dist_from_donor == -39
    assert effect.intron_length == 35622


def test_chr3_97611838_del_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="3:97611838", var="del(4)"
    )

    assert effect.gene == "CRYBG3"
    assert effect.transcript_id == "NM_153605_1"
    assert effect.strand == "+"
    assert effect.effect == "splice-site"
    assert effect.prot_pos == 2525
    assert effect.prot_length == 2970
    assert effect.aa_change is None
    assert effect.which_intron == 11
    assert effect.how_many_introns == 21
    assert effect.dist_from_coding == 0
    assert effect.dist_from_acceptor == 2961
    assert effect.dist_from_donor == 0
    assert effect.intron_length == 2965


def test_chr13_21729291_ins_var(genomic_sequence_2013, gene_models_2013):
    var = (
        "ins(AGTTTTCTTTGTTGCTGACATCTC"
        "GGATGTTCTGTCCATGTTTAAGGAACCTTTTACTGGGTGGCACTGCTTTAAT)"
    )
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="13:21729291", var=var
    )

    assert len(effects) == 2
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "SKA3"
    assert effects_sorted[0].transcript_id == "NM_001166017_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "splice-site"
    assert effects_sorted[0].prot_pos == 374
    assert effects_sorted[0].prot_length == 388
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 7
    assert effects_sorted[0].how_many_introns == 7
    assert effects_sorted[0].dist_from_coding == 1
    assert effects_sorted[0].dist_from_acceptor == 1
    assert effects_sorted[0].dist_from_donor == 2770
    assert effects_sorted[0].intron_length == 2771

    assert effects_sorted[1].gene == "SKA3"
    assert effects_sorted[1].transcript_id == "NM_145061_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "splice-site"
    assert effects_sorted[1].prot_pos == 413
    assert effects_sorted[1].prot_length == 412
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].which_intron == 8
    assert effects_sorted[1].how_many_introns == 8
    assert effects_sorted[1].dist_from_coding == 1
    assert effects_sorted[1].dist_from_acceptor == 1
    assert effects_sorted[1].dist_from_donor == 541
    assert effects_sorted[1].intron_length == 542


def test_chr12_93792633_ins_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="12:93792633",
        var="ins(T)",
    )

    assert len(effects) == 4
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "NUDT4"
    assert effects_sorted[0].transcript_id == "NM_019094_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "splice-site"
    assert effects_sorted[0].prot_pos == 114
    assert effects_sorted[0].prot_length == 180
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 4
    assert effects_sorted[0].how_many_introns == 4
    assert effects_sorted[0].dist_from_coding == 1
    assert effects_sorted[0].dist_from_acceptor == 320
    assert effects_sorted[0].dist_from_donor == 1
    assert effects_sorted[0].intron_length == 321

    assert effects_sorted[1].gene == "NUDT4"
    assert effects_sorted[1].transcript_id == "NM_199040_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "splice-site"
    assert effects_sorted[1].prot_pos == 115
    assert effects_sorted[1].prot_length == 181
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].which_intron == 4
    assert effects_sorted[1].how_many_introns == 4
    assert effects_sorted[1].dist_from_coding == 1
    assert effects_sorted[1].dist_from_acceptor == 320
    assert effects_sorted[1].dist_from_donor == 1
    assert effects_sorted[1].intron_length == 321

    assert effects_sorted[2].gene == "NUDT4P1"
    assert effects_sorted[2].transcript_id == "NR_002212_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "non-coding-intron"
    assert effects_sorted[2].prot_pos is None
    assert effects_sorted[2].prot_length is None
    assert effects_sorted[2].aa_change is None

    assert effects_sorted[3].gene == "NUDT4P2"
    assert effects_sorted[3].transcript_id == "NR_104005_1"
    assert effects_sorted[3].strand == "+"
    assert effects_sorted[3].effect == "non-coding-intron"
    assert effects_sorted[3].prot_pos is None
    assert effects_sorted[3].prot_length is None
    assert effects_sorted[3].aa_change is None


def test_chr17_4086688_del_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="17:4086688", var="del(4)"
    )

    assert len(effects) == 3
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "ANKFY1"
    assert effects_sorted[0].transcript_id == "NM_001257999_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "splice-site"
    assert effects_sorted[0].prot_pos == 693
    assert effects_sorted[0].prot_length == 1211
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 14
    assert effects_sorted[0].how_many_introns == 24
    assert effects_sorted[0].dist_from_coding == 1
    assert effects_sorted[0].dist_from_acceptor == 1043
    assert effects_sorted[0].dist_from_donor == 1
    assert effects_sorted[0].intron_length == 1048

    assert effects_sorted[1].gene == "ANKFY1"
    assert effects_sorted[1].transcript_id == "NM_016376_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "splice-site"
    assert effects_sorted[1].prot_pos == 651
    assert effects_sorted[1].prot_length == 1170
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].which_intron == 14
    assert effects_sorted[1].how_many_introns == 24
    assert effects_sorted[1].dist_from_coding == 1
    assert effects_sorted[1].dist_from_acceptor == 1040
    assert effects_sorted[1].dist_from_donor == 1
    assert effects_sorted[1].intron_length == 1045

    assert effects_sorted[2].gene == "ANKFY1"
    assert effects_sorted[2].transcript_id == "NR_047571_1"
    assert effects_sorted[2].strand == "-"
    assert effects_sorted[2].effect == "non-coding-intron"
    assert effects_sorted[2].prot_pos is None
    assert effects_sorted[2].prot_length is None
    assert effects_sorted[2].aa_change is None


def test_chr21_11049623_sub_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="21:11049623",
        var="sub(T->C)",
    )

    assert len(effects) == 4
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "BAGE4"
    assert effects_sorted[0].transcript_id == "NM_181704_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "splice-site"
    assert effects_sorted[0].prot_pos is None
    assert effects_sorted[0].prot_length == 39
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 3
    assert effects_sorted[0].how_many_introns == 8
    assert effects_sorted[0].dist_from_coding == 1
    assert effects_sorted[0].dist_from_acceptor == 1
    assert effects_sorted[0].dist_from_donor == 8537
    assert effects_sorted[0].intron_length == 8539

    assert effects_sorted[1].gene == "BAGE3"
    assert effects_sorted[1].transcript_id == "NM_182481_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "splice-site"
    assert effects_sorted[1].prot_pos == 94
    assert effects_sorted[1].prot_length == 109
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].which_intron == 3
    assert effects_sorted[1].how_many_introns == 9
    assert effects_sorted[1].dist_from_coding == 1
    assert effects_sorted[1].dist_from_acceptor == 1
    assert effects_sorted[1].dist_from_donor == 8537
    assert effects_sorted[1].intron_length == 8539

    assert effects_sorted[2].gene == "BAGE2"
    assert effects_sorted[2].transcript_id == "NM_182482_1"
    assert effects_sorted[2].strand == "-"
    assert effects_sorted[2].effect == "splice-site"
    assert effects_sorted[2].prot_pos == 94
    assert effects_sorted[2].prot_length == 109
    assert effects_sorted[2].aa_change is None
    assert effects_sorted[2].which_intron == 3
    assert effects_sorted[2].how_many_introns == 9
    assert effects_sorted[2].dist_from_coding == 1
    assert effects_sorted[2].dist_from_acceptor == 1
    assert effects_sorted[2].dist_from_donor == 8537
    assert effects_sorted[2].intron_length == 8539

    assert effects_sorted[3].gene == "BAGE5"
    assert effects_sorted[3].transcript_id == "NM_182484_1"
    assert effects_sorted[3].strand == "-"
    assert effects_sorted[3].effect == "splice-site"
    assert effects_sorted[3].prot_pos is None
    assert effects_sorted[3].prot_length == 39
    assert effects_sorted[3].aa_change is None
    assert effects_sorted[3].which_intron == 3
    assert effects_sorted[3].how_many_introns == 8
    assert effects_sorted[3].dist_from_coding == 1
    assert effects_sorted[3].dist_from_acceptor == 1
    assert effects_sorted[3].dist_from_donor == 8537
    assert effects_sorted[3].intron_length == 8539


def test_chr1_71530819_del_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="1:71530819", var="del(4)"
    )

    assert len(effects) == 3
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "ZRANB2"
    assert effects_sorted[0].transcript_id == "NM_005455_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "splice-site"
    assert effects_sorted[0].prot_pos is None
    assert effects_sorted[0].prot_length == 320
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 10
    assert effects_sorted[0].how_many_introns == 10
    assert effects_sorted[0].dist_from_coding == -2
    assert effects_sorted[0].dist_from_acceptor == -2
    assert effects_sorted[0].dist_from_donor == 538
    assert effects_sorted[0].intron_length == 540

    assert effects_sorted[1].gene == "ZRANB2"
    assert effects_sorted[1].transcript_id == "NM_203350_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "splice-site"
    assert effects_sorted[1].prot_pos == 310
    assert effects_sorted[1].prot_length == 330
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].which_intron == 9
    assert effects_sorted[1].how_many_introns == 9
    assert effects_sorted[1].dist_from_coding == -2
    assert effects_sorted[1].dist_from_acceptor == -2
    assert effects_sorted[1].dist_from_donor == 1636
    assert effects_sorted[1].intron_length == 1638

    assert effects_sorted[2].gene == "ZRANB2-AS1"
    assert effects_sorted[2].transcript_id == "NR_038420_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "non-coding-intron"
    assert effects_sorted[2].prot_pos is None
    assert effects_sorted[2].prot_length is None
    assert effects_sorted[2].aa_change is None


def test_chr1_43917074_del_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="1:43917074",
        var="del(16)",
    )

    assert len(effects) == 4
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "HYI"
    assert effects_sorted[0].transcript_id == "NM_001190880_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "splice-site"
    assert effects_sorted[0].prot_pos == 254
    assert effects_sorted[0].prot_length == 277
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 7
    assert effects_sorted[0].how_many_introns == 7
    assert effects_sorted[0].dist_from_coding == -9
    assert effects_sorted[0].dist_from_acceptor == 91
    assert effects_sorted[0].dist_from_donor == -9
    assert effects_sorted[0].intron_length == 98

    assert effects_sorted[1].gene == "HYI"
    assert effects_sorted[1].transcript_id == "NM_001243526_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "intron"
    assert effects_sorted[1].prot_pos == 273
    assert effects_sorted[1].prot_length == 272
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].which_intron == 8
    assert effects_sorted[1].how_many_introns == 8
    assert effects_sorted[1].dist_from_coding == 9
    assert effects_sorted[1].dist_from_acceptor == 91
    assert effects_sorted[1].dist_from_donor == 9
    assert effects_sorted[1].intron_length == 116

    assert effects_sorted[2].gene == "SZT2"
    assert effects_sorted[2].transcript_id == "NM_015284_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "3'UTR"
    assert effects_sorted[2].prot_pos is None
    assert effects_sorted[2].prot_length == 3375
    assert effects_sorted[2].aa_change is None
    assert effects_sorted[2].dist_from_coding == 923

    assert effects_sorted[3].gene == "HYI"
    assert effects_sorted[3].transcript_id == "NM_031207_1"
    assert effects_sorted[3].strand == "-"
    assert effects_sorted[3].effect == "intron"
    assert effects_sorted[3].prot_pos == 248
    assert effects_sorted[3].prot_length == 247
    assert effects_sorted[3].aa_change is None
    assert effects_sorted[3].which_intron == 7
    assert effects_sorted[3].how_many_introns == 7
    assert effects_sorted[3].dist_from_coding == 9
    assert effects_sorted[3].dist_from_acceptor == 91
    assert effects_sorted[3].dist_from_donor == 9
    assert effects_sorted[3].intron_length == 116


def test_chr1_1653031_del_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="1:1653031", var="del(7)"
    )

    assert len(effects) == 8
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "CDK11A"
    assert effects_sorted[0].transcript_id == "NM_024011_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "splice-site"
    assert effects_sorted[0].prot_pos == 76
    assert effects_sorted[0].prot_length == 780
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 3
    assert effects_sorted[0].how_many_introns == 19
    assert effects_sorted[0].dist_from_coding == -3
    assert effects_sorted[0].dist_from_acceptor == 2136
    assert effects_sorted[0].dist_from_donor == -3
    assert effects_sorted[0].intron_length == 2140

    assert effects_sorted[1].gene == "CDK11B"
    assert effects_sorted[1].transcript_id == "NM_033486_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "splice-site"
    assert effects_sorted[1].prot_pos == 76
    assert effects_sorted[1].prot_length == 780
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].which_intron == 3
    assert effects_sorted[1].how_many_introns == 19
    assert effects_sorted[1].dist_from_coding == -3
    assert effects_sorted[1].dist_from_acceptor == 2136
    assert effects_sorted[1].dist_from_donor == -3
    assert effects_sorted[1].intron_length == 2140

    assert effects_sorted[2].gene == "CDK11B"
    assert effects_sorted[2].transcript_id == "NM_033487_1"
    assert effects_sorted[2].strand == "-"
    assert effects_sorted[2].effect == "splice-site"
    assert effects_sorted[2].prot_pos is None
    assert effects_sorted[2].prot_length == 526
    assert effects_sorted[2].aa_change is None
    assert effects_sorted[2].which_intron == 3
    assert effects_sorted[2].how_many_introns == 17
    assert effects_sorted[2].dist_from_coding == -3
    assert effects_sorted[2].dist_from_acceptor == 2136
    assert effects_sorted[2].dist_from_donor == -3
    assert effects_sorted[2].intron_length == 2140

    assert effects_sorted[3].gene == "CDK11B"
    assert effects_sorted[3].transcript_id == "NM_033488_1"
    assert effects_sorted[3].strand == "-"
    assert effects_sorted[3].effect == "splice-site"
    assert effects_sorted[3].prot_pos == 42
    assert effects_sorted[3].prot_length == 735
    assert effects_sorted[3].aa_change is None
    assert effects_sorted[3].which_intron == 4
    assert effects_sorted[3].how_many_introns == 20
    assert effects_sorted[3].dist_from_coding == -3
    assert effects_sorted[3].dist_from_acceptor == 2136
    assert effects_sorted[3].dist_from_donor == -3
    assert effects_sorted[3].intron_length == 2140

    assert effects_sorted[4].gene == "CDK11B"
    assert effects_sorted[4].transcript_id == "NM_033489_1"
    assert effects_sorted[4].strand == "-"
    assert effects_sorted[4].effect == "splice-site"
    assert effects_sorted[4].prot_pos == 42
    assert effects_sorted[4].prot_length == 746
    assert effects_sorted[4].aa_change is None
    assert effects_sorted[4].which_intron == 4
    assert effects_sorted[4].how_many_introns == 20
    assert effects_sorted[4].dist_from_coding == -3
    assert effects_sorted[4].dist_from_acceptor == 2136
    assert effects_sorted[4].dist_from_donor == -3
    assert effects_sorted[4].intron_length == 2140

    assert effects_sorted[5].gene == "CDK11B"
    assert effects_sorted[5].transcript_id == "NM_033492_1"
    assert effects_sorted[5].strand == "-"
    assert effects_sorted[5].effect == "splice-site"
    assert effects_sorted[5].prot_pos == 76
    assert effects_sorted[5].prot_length == 778
    assert effects_sorted[5].aa_change is None
    assert effects_sorted[5].which_intron == 3
    assert effects_sorted[5].how_many_introns == 19
    assert effects_sorted[5].dist_from_coding == -3
    assert effects_sorted[5].dist_from_acceptor == 2136
    assert effects_sorted[5].dist_from_donor == -3
    assert effects_sorted[5].intron_length == 2140

    assert effects_sorted[6].gene == "CDK11B"
    assert effects_sorted[6].transcript_id == "NM_033493_1"
    assert effects_sorted[6].strand == "-"
    assert effects_sorted[6].effect == "splice-site"
    assert effects_sorted[6].prot_pos == 76
    assert effects_sorted[6].prot_length == 769
    assert effects_sorted[6].aa_change is None
    assert effects_sorted[6].which_intron == 3
    assert effects_sorted[6].how_many_introns == 19
    assert effects_sorted[6].dist_from_coding == -3
    assert effects_sorted[6].dist_from_acceptor == 2136
    assert effects_sorted[6].dist_from_donor == -3
    assert effects_sorted[6].intron_length == 2140

    assert effects_sorted[7].gene == "CDK11A"
    assert effects_sorted[7].transcript_id == "NM_033529_1"
    assert effects_sorted[7].strand == "-"
    assert effects_sorted[7].effect == "splice-site"
    assert effects_sorted[7].prot_pos == 76
    assert effects_sorted[7].prot_length == 770
    assert effects_sorted[7].aa_change is None
    assert effects_sorted[7].which_intron == 3
    assert effects_sorted[7].how_many_introns == 19
    assert effects_sorted[7].dist_from_coding == -3
    assert effects_sorted[7].dist_from_acceptor == 2136
    assert effects_sorted[7].dist_from_donor == -3
    assert effects_sorted[7].intron_length == 2140


def test_chr3_56627768_del_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="3:56627768", var="del(4)"
    )

    assert len(effects) == 3
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "CCDC66"
    assert effects_sorted[0].transcript_id == "NM_001012506_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "splice-site"
    assert effects_sorted[0].prot_pos == 406
    assert effects_sorted[0].prot_length == 914
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 9
    assert effects_sorted[0].how_many_introns == 17
    assert effects_sorted[0].dist_from_coding == -2
    assert effects_sorted[0].dist_from_acceptor == 200
    assert effects_sorted[0].dist_from_donor == -2
    assert effects_sorted[0].intron_length == 202

    assert effects_sorted[1].gene == "CCDC66"
    assert effects_sorted[1].transcript_id == "NM_001141947_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "splice-site"
    assert effects_sorted[1].prot_pos == 440
    assert effects_sorted[1].prot_length == 948
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].which_intron == 9
    assert effects_sorted[1].how_many_introns == 17
    assert effects_sorted[1].dist_from_coding == -2
    assert effects_sorted[1].dist_from_acceptor == 200
    assert effects_sorted[1].dist_from_donor == -2
    assert effects_sorted[1].intron_length == 202

    assert effects_sorted[2].gene == "CCDC66"
    assert effects_sorted[2].transcript_id == "NR_024460_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "non-coding"
    assert effects_sorted[2].prot_pos is None
    assert effects_sorted[2].prot_length is None
    assert effects_sorted[2].aa_change is None


def test_chr3_172538026_del_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="3:172538026",
        var="del(6)",
    )

    assert len(effects) == 3
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "ECT2"
    assert effects_sorted[0].transcript_id == "NM_001258315_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "noEnd"
    assert effects_sorted[0].prot_pos == 915
    assert effects_sorted[0].prot_length == 914
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "ECT2"
    assert effects_sorted[1].transcript_id == "NM_001258316_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "noEnd"
    assert effects_sorted[1].prot_pos == 884
    assert effects_sorted[1].prot_length == 883
    assert effects_sorted[1].aa_change is None

    assert effects_sorted[2].gene == "ECT2"
    assert effects_sorted[2].transcript_id == "NM_018098_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "noEnd"
    assert effects_sorted[2].prot_pos == 884
    assert effects_sorted[2].prot_length == 883
    assert effects_sorted[2].aa_change is None


def test_chr1_29447418_ins_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="1:29447418",
        var="ins(CAGACCC)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "TMEM200B"
    assert effects_sorted[0].transcript_id == "NM_001003682_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "noEnd"
    assert effects_sorted[0].prot_pos == 308
    assert effects_sorted[0].prot_length == 307
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "TMEM200B"
    assert effects_sorted[1].transcript_id == "NM_001171868_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "noEnd"
    assert effects_sorted[1].prot_pos == 308
    assert effects_sorted[1].prot_length == 307
    assert effects_sorted[1].aa_change is None


def test_chr6_99817476_del_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="6:99817476",
        var="del(22)",
    )

    assert effect.gene == "COQ3"
    assert effect.transcript_id == "NM_017421_1"
    assert effect.strand == "-"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 363
    assert effect.prot_length == 369
    assert effect.aa_change is None


def test_last_codon_ins_frameshift_var(
    genomic_sequence_2013, gene_models_2013
):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="7:24727231", var="ins(A)"
    )

    assert effect.gene == "MPP6"
    assert effect.transcript_id == "NM_016447_1"
    assert effect.strand == "+"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 541
    assert effect.prot_length == 540
    assert effect.aa_change is None


def test_chr10_104629323_del_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="10:104629323",
        var="del(29)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "AS3MT"
    assert effects_sorted[0].transcript_id == "NM_020682_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "splice-site"
    assert effects_sorted[0].prot_pos == 1
    assert effects_sorted[0].prot_length == 375
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 1
    assert effects_sorted[0].how_many_introns == 10
    assert effects_sorted[0].dist_from_coding == -28
    assert effects_sorted[0].dist_from_acceptor == 210
    assert effects_sorted[0].dist_from_donor == -28
    assert effects_sorted[0].intron_length == 211

    assert effects_sorted[1].gene == "C10orf32-AS3MT"
    assert effects_sorted[1].transcript_id == "NR_037644_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "non-coding-intron"
    assert effects_sorted[1].prot_pos is None
    assert effects_sorted[1].prot_length is None
    assert effects_sorted[1].aa_change is None


def test_chr1_6694147_del_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="1:6694147", var="del(3)"
    )

    assert effect.gene == "THAP3"
    assert effect.transcript_id == "NM_138350_1"
    assert effect.strand == "+"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 176
    assert effect.prot_length == 175
    assert effect.aa_change is None


def test_chr1_23836374_del_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="1:23836374", var="del(4)"
    )

    assert effect.gene == "E2F2"
    assert effect.transcript_id == "NM_004091_1"
    assert effect.strand == "-"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 437
    assert effect.prot_length == 437
    assert effect.aa_change is None


def test_first_codon_ins_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="1:3527831", var="ins(A)"
    )

    assert effect.gene == "MEGF6"
    assert effect.transcript_id == "NM_001409_1"
    assert effect.strand == "-"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 1541
    assert effect.aa_change is None


def test_chr4_100544005_ins_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="4:100544005",
        var="ins(GAAA)",
    )

    assert effect.gene == "MTTP"
    assert effect.transcript_id == "NM_000253_1"
    assert effect.strand == "+"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 895
    assert effect.prot_length == 894
    assert effect.aa_change is None


def test_chr6_109954111_del_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="6:109954111",
        var="del(4)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "AK9"
    assert effects_sorted[0].transcript_id == "NM_001145128_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "intron"
    assert effects_sorted[0].prot_pos == 419
    assert effects_sorted[0].prot_length == 1911
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].which_intron == 12
    assert effects_sorted[0].how_many_introns == 40
    assert effects_sorted[0].dist_from_coding == 11
    assert effects_sorted[0].dist_from_acceptor == 13671
    assert effects_sorted[0].dist_from_donor == 11
    assert effects_sorted[0].intron_length == 13686

    assert effects_sorted[1].gene == "AK9"
    assert effects_sorted[1].transcript_id == "NM_145025_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "noEnd"
    assert effects_sorted[1].prot_pos == 422
    assert effects_sorted[1].prot_length == 421
    assert effects_sorted[1].aa_change is None


def test_chr16_3070391_del_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="16:3070391",
        var="del(13)",
    )

    assert effect.gene == "TNFRSF12A"
    assert effect.transcript_id == "NM_016639_1"
    assert effect.strand == "+"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 129
    assert effect.aa_change is None


def test_chr1_115316880_del_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="1:115316880",
        var="del(18)",
    )

    assert len(effects) == 4
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "SIKE1"
    assert effects_sorted[0].transcript_id == "NM_001102396_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "noEnd"
    assert effects_sorted[0].prot_pos == 211
    assert effects_sorted[0].prot_length == 211
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "SIKE1"
    assert effects_sorted[1].transcript_id == "NM_025073_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "noEnd"
    assert effects_sorted[1].prot_pos == 207
    assert effects_sorted[1].prot_length == 207
    assert effects_sorted[1].aa_change is None

    assert effects_sorted[2].gene == "SIKE1"
    assert effects_sorted[2].transcript_id == "NR_049741_1"
    assert effects_sorted[2].strand == "-"
    assert effects_sorted[2].effect == "non-coding"
    assert effects_sorted[2].prot_pos is None
    assert effects_sorted[2].prot_length is None
    assert effects_sorted[2].aa_change is None

    assert effects_sorted[3].gene == "SIKE1"
    assert effects_sorted[3].transcript_id == "NR_049742_1"
    assert effects_sorted[3].strand == "-"
    assert effects_sorted[3].effect == "non-coding"
    assert effects_sorted[3].prot_pos is None
    assert effects_sorted[3].prot_length is None
    assert effects_sorted[3].aa_change is None


def test_chr2_47630333_ins_var(genomic_sequence_2013, gene_models_2013):
    var = "ins(GGCGGTGCAGCCGAAGGA)"
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="2:47630333", var=var
    )

    assert len(effects) == 2

    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "MSH2"
    assert effects_sorted[0].transcript_id == "NM_000251_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "noStart"
    assert effects_sorted[0].prot_pos == 1
    assert effects_sorted[0].prot_length == 934
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "MSH2"
    assert effects_sorted[1].transcript_id == "NM_001258281_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "5'UTR-intron"
    assert effects_sorted[1].prot_pos is None
    assert effects_sorted[1].prot_length == 868
    assert effects_sorted[1].aa_change is None


def test_chr2_32853362_ins_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="2:32853362",
        var="ins(TTTTCTAA)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "TTC27"
    assert effects_sorted[0].transcript_id == "NM_001193509_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "5'UTR-intron"
    assert effects_sorted[0].prot_pos is None
    assert effects_sorted[0].prot_length == 793
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "TTC27"
    assert effects_sorted[1].transcript_id == "NM_017735_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "noStart"
    assert effects_sorted[1].prot_pos == 1
    assert effects_sorted[1].prot_length == 843
    assert effects_sorted[1].aa_change is None


def test_chr20_44518889_ins_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="20:44518889",
        var="ins(A)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "NEURL2"
    assert effects_sorted[0].transcript_id == "NM_001278535_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "frame-shift"
    assert effects_sorted[0].prot_pos == 248
    assert effects_sorted[0].prot_length == 261
    # assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "NEURL2"
    assert effects_sorted[1].transcript_id == "NM_080749_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "frame-shift"
    assert effects_sorted[1].prot_pos == 248
    assert effects_sorted[1].prot_length == 285
    # assert effects_sorted[1].aa_change is None


def test_chr9_139839774_ins_var(genomic_sequence_2013, gene_models_2013):
    var = "ins(TGCTGCCGCCACCA)"
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="9:139839774", var=var
    )

    assert effect.gene == "C8G"
    assert effect.transcript_id == "NM_000606_1"
    assert effect.strand == "+"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 202
    assert effect.aa_change is None


def test_chr1_17313765_ins_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="1:17313765", var="ins(C)"
    )

    assert len(effects) == 3
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "ATP13A2"
    assert effects_sorted[0].transcript_id == "NM_001141973_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "frame-shift"
    assert effects_sorted[0].prot_pos == 948
    assert effects_sorted[0].prot_length == 1175
    # assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "ATP13A2"
    assert effects_sorted[1].transcript_id == "NM_001141974_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "frame-shift"
    assert effects_sorted[1].prot_pos == 909
    assert effects_sorted[1].prot_length == 1158
    # assert effects_sorted[1].aa_change is None

    assert effects_sorted[2].gene == "ATP13A2"
    assert effects_sorted[2].transcript_id == "NM_022089_1"
    assert effects_sorted[2].strand == "-"
    assert effects_sorted[2].effect == "frame-shift"
    assert effects_sorted[2].prot_pos == 953
    assert effects_sorted[2].prot_length == 1180
    # assert effects_sorted[2].aa_change is None


def test_chr13_45911524_ins_var(genomic_sequence_2013, gene_models_2013):
    var = "ins(ACATTTTTCCATTTCTAAACCAT)"
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="13:45911524", var=var
    )

    assert effect.gene == "TPT1"
    assert effect.transcript_id == "NM_003295_1"
    assert effect.strand == "-"
    assert effect.effect == "frame-shift"
    assert effect.prot_pos == 172
    assert effect.prot_length == 172
    # assert effect.aa_change is None


def test_chr1_906785_ins_var(genomic_sequence_2013, gene_models_2013):
    var = "ins(GTGGGCCCCTCCCCACT)"
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="1:906785", var=var
    )

    assert len(effects) == 2

    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "PLEKHN1"
    assert effects_sorted[0].transcript_id == "NM_001160184_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "frame-shift"
    assert effects_sorted[0].prot_pos == 276
    assert effects_sorted[0].prot_length == 576
    # assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "PLEKHN1"
    assert effects_sorted[1].transcript_id == "NM_032129_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "frame-shift"
    assert effects_sorted[1].prot_pos == 264
    assert effects_sorted[1].prot_length == 611
    # assert effects_sorted[1].aa_change is None


def test_chr1_45446840_ins_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="1:45446840", var="ins(T)"
    )

    assert len(effects) == 3
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "EIF2B3"
    assert effects_sorted[0].transcript_id == "NM_001166588_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "noStart"
    assert effects_sorted[0].prot_pos == 1
    assert effects_sorted[0].prot_length == 412
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "EIF2B3"
    assert effects_sorted[1].transcript_id == "NM_001261418_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "noStart"
    assert effects_sorted[1].prot_pos == 1
    assert effects_sorted[1].prot_length == 401
    assert effects_sorted[1].aa_change is None

    assert effects_sorted[2].gene == "EIF2B3"
    assert effects_sorted[2].transcript_id == "NM_020365_1"
    assert effects_sorted[2].strand == "-"
    assert effects_sorted[2].effect == "noStart"
    assert effects_sorted[2].prot_pos == 1
    assert effects_sorted[2].prot_length == 452
    assert effects_sorted[2].aa_change is None


def test_chr1_31845860_ins_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="1:31845860",
        var="ins(ATAG)",
    )

    assert effect.gene == "FABP3"
    assert effect.transcript_id == "NM_004102_1"
    assert effect.strand == "-"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 133
    assert effect.aa_change is None


def test_chr1_47775990_del_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="1:47775990", var="del(3)"
    )

    assert len(effects) == 2
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "STIL"
    assert effects_sorted[0].transcript_id == "NM_001048166_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "noStart"
    assert effects_sorted[0].prot_pos == 1
    assert effects_sorted[0].prot_length == 1288
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "STIL"
    assert effects_sorted[1].transcript_id == "NM_003035_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "noStart"
    assert effects_sorted[1].prot_pos == 1
    assert effects_sorted[1].prot_length == 1287
    assert effects_sorted[1].aa_change is None


def test_chr1_120387156_sub_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="1:120387156",
        var="sub(C->T)",
    )

    assert effect.gene == "NBPF7"
    assert effect.transcript_id == "NM_001047980_1"
    assert effect.strand == "-"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 421
    assert effect.aa_change is None


def test_chr11_128868319_ins_var(genomic_sequence_2013, gene_models_2013):
    var = (
        "ins(AATTTCACAATCACCTATTTCTGGTACTTAGCAACATCACAGGTAGATCCTGCCTTC"
        "ATCTTCTGGCATTTC)"
    )
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="11:128868319", var=var
    )

    assert len(effects) == 2
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "ARHGAP32"
    assert effects_sorted[0].transcript_id == "NM_001142685_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "no-frame-shift-newStop"
    assert effects_sorted[0].prot_pos == 350
    assert effects_sorted[0].prot_length == 2087
    assert (
        effects_sorted[0].aa_change
        == "Met->ArgAsnAlaArgArgEndArgGlnAspLeuProValMetLeuLeu"
        "SerThrArgAsnArgEndLeuEndAsnLeu"
    )

    assert effects_sorted[1].gene == "ARHGAP32"
    assert effects_sorted[1].transcript_id == "NM_014715_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "noStart"
    assert effects_sorted[1].prot_pos == 1
    assert effects_sorted[1].prot_length == 1738
    assert effects_sorted[1].aa_change is None


def test_chr1_38061419_del_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="1:38061419",
        var="del(17)",
    )

    assert effect.gene == "GNL2"
    assert effect.transcript_id == "NM_013285_1"
    assert effect.strand == "-"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 731
    assert effect.aa_change is None


def test_first_codon_ins_integenic_var(
    genomic_sequence_2013, gene_models_2013
):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="1:3407092", var="ins(A)"
    )

    assert effect.gene == "MEGF6"
    assert effect.transcript_id == "NM_001409_1"
    assert effect.strand == "-"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 1542
    assert effect.prot_length == 1541
    assert effect.aa_change is None


def test_chr1_92546129_ins_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="1:92546129", var="ins(A)"
    )

    assert effect.gene == "BTBD8"
    assert effect.transcript_id == "NM_183242_1"
    assert effect.strand == "+"
    assert effect.effect == "noStart"
    assert effect.prot_pos == 1
    assert effect.prot_length == 378
    assert effect.aa_change is None


def test_chr1_11740658_ins_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="1:11740658",
        var="ins(TCCT)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "MAD2L2"
    assert effects_sorted[0].transcript_id == "NM_001127325_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "noStart"
    assert effects_sorted[0].prot_pos == 1
    assert effects_sorted[0].prot_length == 211
    assert effects_sorted[0].aa_change is None

    assert effects_sorted[1].gene == "MAD2L2"
    assert effects_sorted[1].transcript_id == "NM_006341_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "noStart"
    assert effects_sorted[1].prot_pos == 1
    assert effects_sorted[1].prot_length == 211
    assert effects_sorted[1].aa_change is None


def test_chr6_161557574_ins_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="6:161557574",
        var="ins(AGTC)",
    )

    assert effect.gene == "AGPAT4"
    assert effect.transcript_id == "NM_020133_1"
    assert effect.strand == "-"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 379
    assert effect.prot_length == 378
    assert effect.aa_change is None


def test_chr11_123847404_ins_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="11:123847404",
        var="ins(T)",
    )

    assert effect.gene is None
    assert effect.transcript_id is None
    assert effect.strand is None
    assert effect.effect == "intergenic"
    assert effect.prot_pos is None
    assert effect.prot_length is None
    assert effect.aa_change is None


def test_chr1_26158517_ins_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="1:26158517",
        var="ins(ACA)",
    )

    assert len(effects) == 4
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "MTFR1L"
    assert effects_sorted[0].transcript_id == "NM_001099625_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "noEnd"
    assert effects_sorted[0].prot_pos == 293
    assert effects_sorted[0].prot_length == 292
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[1].gene == "MTFR1L"
    assert effects_sorted[1].transcript_id == "NM_001099626_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "noEnd"
    assert effects_sorted[1].prot_pos == 293
    assert effects_sorted[1].prot_length == 292
    assert effects_sorted[1].aa_change is None

    assert effects_sorted[2].gene == "MTFR1L"
    assert effects_sorted[2].transcript_id == "NM_001099627_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "3'UTR"
    assert effects_sorted[2].prot_pos is None
    assert effects_sorted[2].prot_length == 205
    assert effects_sorted[2].aa_change is None
    assert effects_sorted[2].dist_from_coding == 152

    assert effects_sorted[3].gene == "MTFR1L"
    assert effects_sorted[3].transcript_id == "NM_019557_1"
    assert effects_sorted[3].strand == "+"
    assert effects_sorted[3].effect == "noEnd"
    assert effects_sorted[3].prot_pos == 293
    assert effects_sorted[3].prot_length == 292
    assert effects_sorted[3].aa_change is None


def test_last_codon_ins_intergenic_var(
    genomic_sequence_2013, gene_models_2013
):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="7:24727232", var="ins(A)"
    )

    assert effect.gene == "MPP6"
    assert effect.transcript_id == "NM_016447_1"
    assert effect.strand == "+"
    assert effect.effect == "3'UTR"
    assert effect.prot_pos is None
    assert effect.prot_length == 540
    assert effect.aa_change is None
    assert effect.dist_from_coding == 0


def test_chr7_149461804_del_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="7:149461804",
        var="del(1)",
    )

    assert effect.gene == "ZNF467"
    assert effect.transcript_id == "NM_207336_1"
    assert effect.strand == "-"
    assert effect.effect == "3'UTR"
    assert effect.prot_pos is None
    assert effect.prot_length == 595
    assert effect.aa_change is None
    assert effect.dist_from_coding == 0


def test_chr1_44686290_ins_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="1:44686290", var="ins(A)"
    )

    assert len(effects) == 3
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "DMAP1"
    assert effects_sorted[0].transcript_id == "NM_001034023_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "3'UTR"
    assert effects_sorted[0].prot_pos is None
    assert effects_sorted[0].prot_length == 467
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].dist_from_coding == 0

    assert effects_sorted[1].gene == "DMAP1"
    assert effects_sorted[1].transcript_id == "NM_001034024_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "3'UTR"
    assert effects_sorted[1].prot_pos is None
    assert effects_sorted[1].prot_length == 467
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].dist_from_coding == 0

    assert effects_sorted[2].gene == "DMAP1"
    assert effects_sorted[2].transcript_id == "NM_019100_1"
    assert effects_sorted[2].strand == "+"
    assert effects_sorted[2].effect == "3'UTR"
    assert effects_sorted[2].prot_pos is None
    assert effects_sorted[2].prot_length == 467
    assert effects_sorted[2].aa_change is None
    assert effects_sorted[2].dist_from_coding == 0


def test_chr1_26142208_ins_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="1:26142208",
        var="ins(AG)",
    )

    assert len(effects) == 2
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "SEPN1"
    assert effects_sorted[0].transcript_id == "NM_020451_1"
    assert effects_sorted[0].strand == "+"
    assert effects_sorted[0].effect == "3'UTR"
    assert effects_sorted[0].prot_pos is None
    assert effects_sorted[0].prot_length == 590
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].dist_from_coding == 0

    assert effects_sorted[1].gene == "SEPN1"
    assert effects_sorted[1].transcript_id == "NM_206926_1"
    assert effects_sorted[1].strand == "+"
    assert effects_sorted[1].effect == "3'UTR"
    assert effects_sorted[1].prot_pos is None
    assert effects_sorted[1].prot_length == 556
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].dist_from_coding == 0


def test_chr12_125396262_ins_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="12:125396262",
        var="ins(T)",
    )

    assert effect.gene == "UBC"
    assert effect.transcript_id == "NM_021009_1"
    assert effect.strand == "-"
    assert effect.effect == "3'UTR"
    assert effect.prot_pos is None
    assert effect.prot_length == 685
    assert effect.aa_change is None
    assert effect.dist_from_coding == 0


def test_chr1_16890438_del_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="1:16890438", var="del(1)"
    )

    assert effect.gene == "NBPF1"
    assert effect.transcript_id == "NM_017940_1"
    assert effect.strand == "-"
    assert effect.effect == "3'UTR"
    assert effect.prot_pos is None
    assert effect.prot_length == 1141
    assert effect.aa_change is None
    assert effect.dist_from_coding == 0


def test_chr1_20440608_ins_var(genomic_sequence_2013, gene_models_2013):
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="1:20440608", var="ins(T)"
    )

    assert len(effects) == 2
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "PLA2G2D"
    assert effects_sorted[0].transcript_id == "NM_001271814_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "3'UTR"
    assert effects_sorted[0].prot_pos is None
    assert effects_sorted[0].prot_length == 62
    assert effects_sorted[0].aa_change is None
    assert effects_sorted[0].dist_from_coding == 141

    assert effects_sorted[1].gene == "PLA2G2D"
    assert effects_sorted[1].transcript_id == "NM_012400_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "3'UTR"
    assert effects_sorted[1].prot_pos is None
    assert effects_sorted[1].prot_length == 145
    assert effects_sorted[1].aa_change is None
    assert effects_sorted[1].dist_from_coding == 0


def test_chr11_62931298_ins_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="11:62931298",
        var="ins(C)",
    )

    assert effect.gene is None
    assert effect.transcript_id is None
    assert effect.strand is None
    assert effect.effect == "intergenic"
    assert effect.prot_pos is None
    assert effect.prot_length is None
    assert effect.aa_change is None


def test_chr1_20490475_del_var(genomic_sequence_2013, gene_models_2013):
    [effect] = EffectAnnotator.annotate_variant(
        gene_models_2013,
        genomic_sequence_2013,
        loc="1:20490475",
        var="del(18)",
    )

    assert effect.gene == "PLA2G2C"
    assert effect.transcript_id == "NM_001105572_1"
    assert effect.strand == "-"
    assert effect.effect == "noEnd"
    assert effect.prot_pos == 149
    assert effect.prot_length == 150
    assert effect.aa_change is None


def test_chr13_21729290_ins_var(genomic_sequence_2013, gene_models_2013):
    var = "ins(CAGTTTTCTTTGTTGCTGACATCTCGGATGTTCTGTCCATGTTTAAGGAACCTTTTA)"
    effects = EffectAnnotator.annotate_variant(
        gene_models_2013, genomic_sequence_2013, loc="13:21729290", var=var
    )

    assert len(effects) == 2
    effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

    assert effects_sorted[0].gene == "SKA3"
    assert effects_sorted[0].transcript_id == "NM_001166017_1"
    assert effects_sorted[0].strand == "-"
    assert effects_sorted[0].effect == "no-frame-shift-newStop"
    assert effects_sorted[0].prot_pos == 373
    assert effects_sorted[0].prot_length == 388
    assert (
        effects_sorted[0].aa_change
        == "->EndLysValProEndThrTrpThrGluHisProArgCysGlnGlnGln"
        "ArgLysLeu"
    )

    assert effects_sorted[1].gene == "SKA3"
    assert effects_sorted[1].transcript_id == "NM_145061_1"
    assert effects_sorted[1].strand == "-"
    assert effects_sorted[1].effect == "noEnd"
    assert effects_sorted[1].prot_pos == 413
    assert effects_sorted[1].prot_length == 412
    assert effects_sorted[1].aa_change is None
