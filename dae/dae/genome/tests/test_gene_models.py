import pytest

import os

from dae.GeneModelFiles import (
    GeneModelDB,
    gtfGeneModelParser,
    refSeqParser,
    refFlatParser,
    ccdsParser,
    knownGeneParser,
    defaultGeneModelParser,
    load_default_gene_models_format,
    load_ref_flat_gene_models_format,
    load_ref_seq_gene_models_format,
    load_ccds_gene_models_format,
    load_known_gene_models_format,
    load_gtf_gene_modles_format,
    probe_header,
    probe_columns,
    infer_gene_model_parser,
    load_gene_models,
    GENE_MODELS_FORMAT_COLUMNS,
)


def test_gene_models_from_gtf(fixture_dirname):
    gtf_filename = fixture_dirname("gene_models/test_ref_gene.gtf")
    print(gtf_filename)

    assert os.path.exists(gtf_filename)
    gm = GeneModelDB()
    gtfGeneModelParser(gm, gtf_filename)

    assert len(gm.transcriptModels) == 12
    assert len(gm._geneModels) == 12

    gm1 = load_gtf_gene_modles_format(gtf_filename)
    assert gm1 is not None


@pytest.mark.parametrize(
    "filename",
    [
        "gene_models/test_gencode_selenon.gtf",
        "gene_models/test_ref_gene.gtf",
        "gene_models/test_gencode.gtf",
    ],
)
def test_gene_models_from_gtf_selenon(fixture_dirname, filename):
    gtf_filename = fixture_dirname(filename)
    print(gtf_filename)

    gm = GeneModelDB()
    gtfGeneModelParser(gm, gtf_filename)

    # assert len(gm.transcriptModels) == 5
    # assert len(gm._geneModels) == 1

    gm1 = load_gtf_gene_modles_format(gtf_filename)
    assert gm1 is not None
    # assert len(gm1.transcriptModels) == 5
    # assert len(gm1._geneModels) == 1

    for tr_id, tm in gm.transcriptModels.items():
        tm1 = gm1.transcriptModels[tr_id]

        assert tm.tr_id == tm1.tr_id
        assert tm.tr_name == tm1.tr_name
        assert tm.gene == tm1.gene
        assert tm.chrom == tm1.chrom
        assert tm.cds == tm1.cds
        assert tm.strand == tm1.strand
        assert tm.tx == tm1.tx
        assert len(tm.utrs) == len(tm1.utrs), (len(tm.utrs), len(tm1.utrs))
        assert tm.utrs == tm1.utrs, (tm.utrs, tm1.utrs)
        assert tm.start_codon == tm1.start_codon
        assert tm.stop_codon == tm1.stop_codon

        assert len(tm.exons) == len(tm1.exons)
        for index, (exon, exon1) in enumerate(zip(tm.exons, tm1.exons)):
            assert exon.start == exon1.start, (
                tm.exons[: index + 2],
                tm1.exons[: index + 2],
            )
            assert exon.stop == exon1.stop
            assert exon.frame == exon1.frame
            assert exon.number == exon1.number
            assert exon.cds_start == exon1.cds_start
            assert exon.cds_stop == exon1.cds_stop


def test_gene_models_from_ref_gene_ref_seq(fixture_dirname):
    filename = fixture_dirname("gene_models/test_ref_gene.txt")
    assert os.path.exists(filename)
    gm = GeneModelDB()
    refSeqParser(gm, filename)
    assert len(gm.transcriptModels) == 12
    assert len(gm._geneModels) == 12

    gm1 = load_ref_seq_gene_models_format(filename)
    assert gm1 is not None
    assert len(gm1.transcriptModels) == 12
    assert len(gm1._geneModels) == 12


def test_gene_models_from_ref_seq_orig(fixture_dirname):
    filename = fixture_dirname("gene_models/test_ref_seq_hg38.txt")
    assert os.path.exists(filename)
    gm = GeneModelDB()
    refSeqParser(gm, filename)
    assert len(gm.transcriptModels) == 20
    assert len(gm._geneModels) == 8

    gm1 = load_ref_seq_gene_models_format(filename)
    assert gm1 is not None
    assert len(gm1.transcriptModels) == 20
    assert len(gm1._geneModels) == 8

    assert gm._geneModels.keys() == gm1._geneModels.keys()
    assert gm.transcriptModels.keys() == gm1.transcriptModels.keys()


def test_gene_models_from_gencode(fixture_dirname):
    filename = fixture_dirname("gene_models/test_gencode.gtf")
    assert os.path.exists(filename)
    gm = GeneModelDB()
    gtfGeneModelParser(gm, filename)
    assert len(gm.transcriptModels) == 19
    assert len(gm._geneModels) == 10


@pytest.mark.parametrize(
    "filename",
    [
        "gene_models/test_ref_flat.txt",
        "gene_models/test_ref_flat_no_header.txt",
    ],
)
def test_gene_models_from_ref_flat(fixture_dirname, filename):
    filename = fixture_dirname(filename)
    assert os.path.exists(filename)
    gm = GeneModelDB()
    refFlatParser(gm, filename)
    assert len(gm.transcriptModels) == 19
    assert len(gm._geneModels) == 19

    gm1 = load_ref_flat_gene_models_format(filename)
    assert gm1 is not None
    assert len(gm1.transcriptModels) == 19
    assert len(gm1._geneModels) == 19

    assert gm._geneModels.keys() == gm1._geneModels.keys()
    assert gm.transcriptModels.keys() == gm1.transcriptModels.keys()


def test_gene_models_from_ccds(fixture_dirname):
    filename = fixture_dirname("gene_models/test_ccds.txt")
    gene_mapping_file = fixture_dirname("gene_models/ccds_id2sym.txt.gz")

    assert os.path.exists(filename)
    gm = GeneModelDB()
    ccdsParser(gm, filename, gene_mapping_file=gene_mapping_file)
    assert len(gm.transcriptModels) == 20
    assert len(gm._geneModels) == 15

    gm1 = load_ccds_gene_models_format(
        filename, gene_mapping_file=gene_mapping_file
    )

    assert gm1 is not None
    assert len(gm1.transcriptModels) == 20
    assert len(gm1._geneModels) == 15

    assert gm._geneModels.keys() == gm1._geneModels.keys()
    assert gm.transcriptModels.keys() == gm1.transcriptModels.keys()


def test_gene_models_probe_header(fixture_dirname):
    filename = fixture_dirname("gene_models/test_ccds.txt")
    assert not probe_header(filename, GENE_MODELS_FORMAT_COLUMNS["ccds"])
    assert probe_columns(filename, GENE_MODELS_FORMAT_COLUMNS["ccds"])

    filename = fixture_dirname("gene_models/test_ref_flat.txt")
    assert probe_header(filename, GENE_MODELS_FORMAT_COLUMNS["refflat"])


def test_gene_models_from_known_gene(fixture_dirname):
    filename = fixture_dirname("gene_models/test_known_gene.txt")
    gene_mapping_file = fixture_dirname("gene_models/kg_id2sym.txt.gz")

    assert os.path.exists(filename)
    gm = GeneModelDB()
    knownGeneParser(gm, filename, gene_mapping_file=gene_mapping_file)
    assert len(gm.transcriptModels) == 20
    assert len(gm._geneModels) == 14

    gm1 = load_known_gene_models_format(
        filename, gene_mapping_file=gene_mapping_file
    )

    assert gm1 is not None
    assert len(gm1.transcriptModels) == 20
    assert len(gm1._geneModels) == 14

    assert gm._geneModels.keys() == gm1._geneModels.keys()
    assert gm.transcriptModels.keys() == gm1.transcriptModels.keys()


def test_gene_models_from_default_ref_gene_2013(fixture_dirname):
    filename = fixture_dirname("gene_models/test_default_ref_gene_201309.txt")
    assert os.path.exists(filename)
    gm = GeneModelDB()
    defaultGeneModelParser(gm, filename)
    assert len(gm.transcriptModels) == 19
    assert len(gm._geneModels) == 19

    gm1 = load_default_gene_models_format(filename)
    assert gm1 is not None
    assert len(gm1.transcriptModels) == 19
    assert len(gm1._geneModels) == 19


def test_gene_models_from_default_with_transcript_orig_id(fixture_dirname):
    filename = fixture_dirname(
        "gene_models/test_default_ref_gene_20190220.txt"
    )
    gm1 = load_default_gene_models_format(filename)
    assert gm1 is not None
    assert len(gm1.transcriptModels) == 19
    assert len(gm1._geneModels) == 19

    for tm in gm1.transcriptModels.values():
        assert tm.tr_id != tm.tr_name


def test_default_gene_models_loader_ref_seq_2019(genomes_db_2019):
    genome_id = genomes_db_2019.config.genomes.default_genome
    genome_config = getattr(genomes_db_2019.config.genome, genome_id)
    ref_seq_gene_model = getattr(genome_config.gene_model, "RefSeq")

    gm = load_default_gene_models_format(ref_seq_gene_model.file)
    assert gm is not None


def test_default_gene_models_loader_ref_seq_2013(genomes_db_2013):
    genome_id = genomes_db_2013.config.genomes.default_genome
    genome_config = getattr(genomes_db_2013.config.genome, genome_id)
    ref_seq_gene_model = getattr(genome_config.gene_model, "RefSeq2013")

    gm = load_default_gene_models_format(ref_seq_gene_model.file)
    assert gm is not None

    gm_yoonha = GeneModelDB()
    defaultGeneModelParser(gm_yoonha, ref_seq_gene_model.file)
    assert len(gm.transcriptModels) == len(gm_yoonha.transcriptModels)


@pytest.mark.parametrize(
    "filename,fileformat",
    [
        ("gene_models/test_ref_flat.txt", "refflat"),
        ("gene_models/test_ref_flat_no_header.txt", "refflat"),
        ("gene_models/test_ccds.txt", "ccds"),
        ("gene_models/test_ref_gene.txt", "refseq"),
        ("gene_models/test_ref_seq_hg38.txt", "refseq"),
        ("gene_models/test_known_gene.txt", "knowngene"),
        ("gene_models/test_default_ref_gene_201309.txt", "default"),
    ],
)
def test_load_gene_models(fixture_dirname, filename, fileformat):

    filename = fixture_dirname(filename)
    gm = load_gene_models(filename, fileformat=fileformat)
    assert gm is not None


@pytest.mark.parametrize(
    "filename,fileformat",
    [
        ("gene_models/test_ref_flat.txt", "refflat"),
        ("gene_models/test_ref_flat_no_header.txt", "refflat"),
        ("gene_models/test_ccds.txt", "ccds"),
        ("gene_models/test_ref_gene.txt", "refseq"),
        ("gene_models/test_ref_seq_hg38.txt", "refseq"),
        ("gene_models/test_known_gene.txt", "knowngene"),
        ("gene_models/test_default_ref_gene_201309.txt", "default"),
    ],
)
def test_infer_gene_models(fixture_dirname, filename, fileformat):

    filename = fixture_dirname(filename)
    inferred_fileformat = infer_gene_model_parser(
        filename, fileformat=fileformat
    )
    assert inferred_fileformat is not None
    assert inferred_fileformat == fileformat
