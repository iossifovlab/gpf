# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import pathlib

from dae.testing.ala_tox4_import import ala_tox4_genome, ala_tox4_genes


def test_ala_tox4_genome(tmp_path: pathlib.Path) -> None:
    genome = ala_tox4_genome(tmp_path)
    assert genome is not None

    assert genome.chromosomes == ["chr14"]
    assert genome.get_chrom_length("chr14") == 90

    assert genome.get_sequence("chr14", 10, 10) == "G"
    assert genome.get_sequence("chr14", 24, 25) == "AG"
    assert genome.get_sequence("chr14", 37, 38) == "GG"
    assert genome.get_sequence("chr14", 45, 46) == "GA"
    assert genome.get_sequence("chr14", 50, 51) == "TC"
    assert genome.get_sequence("chr14", 52, 71) == "CATACAACCATGGTGAAATA"
    assert genome.get_sequence("chr14", 72, 84) == "GTCCTTCCTGTTA"


def test_ala_tox4_genes(tmp_path: pathlib.Path) -> None:
    gene_models = ala_tox4_genes(tmp_path)
    gene_models.load()

    assert gene_models is not None

    # only one gene - g4
    assert gene_models.gene_models is not None
    assert len(gene_models.gene_models) == 1
    assert "g4" in gene_models.gene_models

    # only one transctipt in g4
    assert len(gene_models.gene_models["g4"]) == 1
    trans = gene_models.gene_models["g4"][0]

    assert trans.strand == "+"
    assert trans.chrom == "chr14"

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
