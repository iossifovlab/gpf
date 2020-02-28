import pytest

import os

from dae.GeneModelFiles import (
    GeneModelDB,
    gtfGeneModelParser,
    refSeqParser,
    refFlatParser,
    ccdsParser,
    knownGeneParser,
)


def test_gene_models_from_gtf(fixture_dirname):
    gtf_filename = fixture_dirname("gene_models/test_ref_gene.gtf")
    assert os.path.exists(gtf_filename)
    gm = GeneModelDB()
    gtfGeneModelParser(gm, gtf_filename)

    assert len(gm.transcriptModels) == 12
    assert len(gm._geneModels) == 12


def test_gene_models_from_ref_gene(fixture_dirname):
    filename = fixture_dirname("gene_models/test_ref_gene.txt")
    assert os.path.exists(filename)
    gm = GeneModelDB()
    refSeqParser(gm, filename)
    assert len(gm.transcriptModels) == 12
    assert len(gm._geneModels) == 12


def test_gene_models_from_gencode(fixture_dirname):
    filename = fixture_dirname("gene_models/test_gencode.gtf")
    assert os.path.exists(filename)
    gm = GeneModelDB()
    gtfGeneModelParser(gm, filename)
    assert len(gm.transcriptModels) == 19
    assert len(gm._geneModels) == 10


def test_gene_models_from_ref_flat(fixture_dirname):
    filename = fixture_dirname("gene_models/test_ref_flat.txt")
    assert os.path.exists(filename)
    gm = GeneModelDB()
    refFlatParser(gm, filename)
    assert len(gm.transcriptModels) == 19
    assert len(gm._geneModels) == 19


@pytest.mark.xfail(reason="CCDS file format parser is broken")
def test_gene_models_from_ccds(fixture_dirname):
    filename = fixture_dirname("gene_models/test_ccds.txt")
    assert os.path.exists(filename)
    gm = GeneModelDB()
    ccdsParser(gm, filename, gene_mapping_file=None)
    assert len(gm.transcriptModels) == 19
    assert len(gm._geneModels) == 19


@pytest.mark.xfail(reason="KnownGene file format parser is broken")
def test_gene_models_from_known_gene(fixture_dirname):
    filename = fixture_dirname("gene_models/test_known_gene.txt")
    assert os.path.exists(filename)
    gm = GeneModelDB()
    knownGeneParser(gm, filename, gene_mapping_file=None)
    assert len(gm.transcriptModels) == 19
    assert len(gm._geneModels) == 19


@pytest.mark.xfail(reason="RefSeq file format parser is broken")
def test_gene_models_from_ref_gene_2013(fixture_dirname):
    filename = fixture_dirname("gene_models/test_ref_gene_201309.txt")
    assert os.path.exists(filename)
    gm = GeneModelDB()
    refSeqParser(gm, filename)
    assert len(gm.transcriptModels) == 19
    assert len(gm._geneModels) == 19
