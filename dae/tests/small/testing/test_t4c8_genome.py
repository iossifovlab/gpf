# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import pathlib

import pytest

from dae.effect_annotation.annotator import EffectAnnotator
from dae.testing.t4c8_import import t4c8_genes, t4c8_genome


def test_t4c8_genome(tmp_path: pathlib.Path) -> None:
    genome = t4c8_genome(tmp_path)
    assert genome is not None

    assert genome.chromosomes == ["chr1"]
    assert genome.get_chrom_length("chr1") == 210

    assert genome.get_sequence("chr1", 10, 10) == "G"
    assert genome.get_sequence("chr1", 24, 25) == "AG"
    assert genome.get_sequence("chr1", 37, 38) == "GG"
    assert genome.get_sequence("chr1", 45, 46) == "GA"
    assert genome.get_sequence("chr1", 50, 51) == "TC"
    assert genome.get_sequence("chr1", 52, 71) == "CATACAACCATGGTGAAATA"
    assert genome.get_sequence("chr1", 72, 84) == "GTCCTTCCTGTTA"


def test_t4_gene_model(tmp_path: pathlib.Path) -> None:
    gene_models = t4c8_genes(tmp_path)

    assert gene_models is not None

    # only two genes - t4, c8
    assert gene_models.gene_models is not None
    assert len(gene_models.gene_models) == 2
    assert "t4" in gene_models.gene_models

    # only one transctipt in t4
    assert len(gene_models.gene_models["t4"]) == 1
    trans = gene_models.gene_models["t4"][0]

    assert trans.strand == "+"
    assert trans.chrom == "chr1"

    assert trans.cds == (11, 71)
    assert trans.tx == (6, 84)

    assert len(trans.exons) == 3

    ex0 = trans.exons[0]
    assert ex0.start == 6
    assert ex0.stop == 16

    ex1 = trans.exons[1]
    assert ex1.start == 26
    assert ex1.stop == 37

    ex2 = trans.exons[2]
    assert ex2.start == 46
    assert ex2.stop == 84


def test_t4c8_c8_genome(tmp_path: pathlib.Path) -> None:
    genome = t4c8_genome(tmp_path)
    assert genome is not None

    assert genome.chromosomes == ["chr1"]
    assert genome.get_chrom_length("chr1") == 210

    assert genome.get_sequence("chr1", 91, 100) == "NNNNNNNNAT"
    assert genome.get_sequence("chr1", 101, 110) == "AAGGATGGGG"
    assert genome.get_sequence("chr1", 112, 114) == "TTC"
    assert genome.get_sequence("chr1", 130, 132) == "GAC"
    assert genome.get_sequence("chr1", 131, 133) == "ACC"

    assert genome.get_sequence("chr1", 145, 147) == "CCT"
    assert genome.get_sequence("chr1", 155, 157) == "ATT"
    assert genome.get_sequence("chr1", 158, 160) == "GGG"
    assert genome.get_sequence("chr1", 167, 169) == "CAT"


@pytest.mark.parametrize("chrom, pos, ref, alt, expected", [
    ("chr1", 204, "C", "T", "5'UTR"),
    ("chr1", 196, "C", "T", "5'UTR"),

    ("chr1", 195, "C", "T", "splice-site"),
    ("chr1", 194, "A", "T", "splice-site"),
    ("chr1", 185, "T", "C", "splice-site"),
    ("chr1", 184, "C", "A", "splice-site"),
    ("chr1", 183, "C", "A", "5'UTR"),
    ("chr1", 170, "C", "A", "5'UTR"),

    ("chr1", 169, "T", "C", "noStart"),
    ("chr1", 168, "A", "C", "noStart"),
    ("chr1", 167, "C", "A", "noStart"),

    ("chr1", 115, "A", "C", "noEnd"),
    ("chr1", 114, "C", "A", "noEnd"),
    ("chr1", 113, "T", "A", "noEnd"),

    ("chr1", 114, "C", "T", "synonymous"),
    ("chr1", 114, "C", "G", "noEnd"),

    ("chr1", 145, "C", "T", "splice-site"),
    ("chr1", 144, "A", "T", "splice-site"),
    ("chr1", 134, "C", "T", "splice-site"),
    ("chr1", 135, "T", "A", "splice-site"),

    ("chr1", 112, "T", "A", "3'UTR"),
    ("chr1", 111, "C", "A", "3'UTR"),
    ("chr1", 101, "A", "G", "3'UTR"),

    ("chr1", 100, "T", "G", "intergenic"),

    ("chr1", 117, "T", "A", "missense"),
    ("chr1", 117, "T", "C", "missense"),
    ("chr1", 117, "T", "G", "missense"),

    ("chr1", 118, "C", "A", "missense"),
    ("chr1", 118, "C", "G", "missense"),
    ("chr1", 118, "C", "T", "missense"),

    ("chr1", 119, "A", "C", "missense"),
    ("chr1", 119, "A", "G", "synonymous"),
    ("chr1", 119, "A", "T", "missense"),

    ("chr1", 122, "A", "C", "synonymous"),
    ("chr1", 122, "A", "G", "synonymous"),
    ("chr1", 122, "A", "T", "synonymous"),

    ("chr1", 52, "C", "A", "missense"),
    ("chr1", 52, "C", "G", "missense"),
    ("chr1", 52, "C", "T", "missense"),

    ("chr1", 53, "A", "C", "missense"),
    ("chr1", 53, "A", "G", "missense"),
    ("chr1", 53, "A", "T", "missense"),

    ("chr1", 54, "T", "A", "missense"),
    ("chr1", 54, "T", "C", "synonymous"),
    ("chr1", 54, "T", "G", "missense"),

    ("chr1", 55, "A", "C", "missense"),
    ("chr1", 55, "A", "G", "missense"),
    ("chr1", 55, "A", "T", "missense"),

    ("chr1", 56, "C", "A", "missense"),
    ("chr1", 56, "C", "G", "missense"),
    ("chr1", 56, "C", "T", "missense"),

    ("chr1", 57, "A", "C", "synonymous"),
    ("chr1", 57, "A", "G", "synonymous"),
    ("chr1", 57, "A", "T", "synonymous"),

])
def test_t4c8_c8_gene_effects(
        chrom: str, pos: int, ref: str, alt: str, expected: str,
        tmp_path: pathlib.Path) -> None:

    genome = t4c8_genome(tmp_path)
    gene_models = t4c8_genes(tmp_path)

    effect_annotator = EffectAnnotator(genome, gene_models)
    assert effect_annotator is not None

    result = effect_annotator.do_annotate_variant(
        chrom=chrom, pos=pos, ref=ref, alt=alt)
    assert result is not None

    assert len(result) == 1
    effect = result[0]
    assert effect.effect == expected
