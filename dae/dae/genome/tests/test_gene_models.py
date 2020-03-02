import pytest

import os

from dae.GeneModelFiles import (
    GeneModelDB,
    gtfGeneModelParser,
    refSeqParser,
    refFlatParser,
    ccdsParser,
    knownGeneParser,
    load_default_gene_models_format,
    defaultGeneModelParser,
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


def test_default_gene_models_loader_ref_seq_2019(genomes_db_2019):
    genome_id = genomes_db_2019.config.genomes.default_genome
    genome_config = getattr(genomes_db_2019.config.genome, genome_id)
    ref_seq_gene_model = getattr(genome_config.gene_model, "RefSeq")

    gm = load_default_gene_models_format(ref_seq_gene_model.file)
    assert gm is not None


def test_default_gene_models_loader_ref_seq_2013(genomes_db_2019):
    genome_id = genomes_db_2019.config.genomes.default_genome
    genome_config = getattr(genomes_db_2019.config.genome, genome_id)
    ref_seq_gene_model = getattr(genome_config.gene_model, "RefSeq2013")

    gm = load_default_gene_models_format(ref_seq_gene_model.file)
    assert gm is not None

    gm_yoonha = GeneModelDB()
    defaultGeneModelParser(gm_yoonha, ref_seq_gene_model.file)
    assert len(gm.transcriptModels) == len(gm_yoonha.transcriptModels)
