# pylint: disable=W0621,C0114,C0116,W0212,W0613
import gzip
import os

import pytest

from dae.genomic_resources.gene_models import build_gene_models_from_file
# from dae.genomic_resources.gene_models import _open_file


def test_gene_models_from_gtf(fixture_dirname):
    gtf_filename = fixture_dirname("gene_models/test_ref_gene.gtf")
    print(gtf_filename)

    assert os.path.exists(gtf_filename)

    gene_models = build_gene_models_from_file(gtf_filename, file_format="gtf")
    gene_models.load()
    assert gene_models is not None
    assert len(gene_models.transcript_models) == 12
    assert len(gene_models.gene_models) == 12


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

    gene_models = build_gene_models_from_file(gtf_filename, file_format="gtf")
    gene_models.load()
    assert gene_models is not None


def test_gene_models_from_ref_gene_ref_seq(fixture_dirname):
    filename = fixture_dirname("gene_models/test_ref_gene.txt")
    assert os.path.exists(filename)

    gene_models = build_gene_models_from_file(filename, file_format="refseq")
    gene_models.load()
    assert len(gene_models.transcript_models) == 12
    assert len(gene_models.gene_models) == 12


def test_gene_models_from_ref_seq_orig(fixture_dirname):
    filename = fixture_dirname("gene_models/test_ref_seq_hg38.txt")
    assert os.path.exists(filename)

    gene_models = build_gene_models_from_file(filename, file_format="refseq")
    gene_models.load()
    assert gene_models is not None
    assert len(gene_models.transcript_models) == 20
    assert len(gene_models.gene_models) == 8


def test_gene_models_from_gencode(fixture_dirname):
    filename = fixture_dirname("gene_models/test_gencode.gtf")
    assert os.path.exists(filename)
    gene_models = build_gene_models_from_file(filename, "gtf")
    gene_models.load()
    assert len(gene_models.transcript_models) == 19
    assert len(gene_models.gene_models) == 10


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
    gene_models = build_gene_models_from_file(filename, "refflat")
    gene_models.load()
    assert len(gene_models.transcript_models) == 19
    assert len(gene_models.gene_models) == 19


def test_gene_models_from_ccds(fixture_dirname):
    filename = fixture_dirname("gene_models/test_ccds.txt")
    gene_mapping_file = fixture_dirname("gene_models/ccds_id2sym.txt.gz")

    assert os.path.exists(filename)

    gene_models = build_gene_models_from_file(
        filename, file_format="ccds", gene_mapping_file_name=gene_mapping_file)
    gene_models.load()
    assert len(gene_models.transcript_models) == 20
    assert len(gene_models.gene_models) == 15

    assert gene_models is not None
    assert len(gene_models.transcript_models) == 20
    assert len(gene_models.gene_models) == 15


# def test_gene_models_probe_header(fixture_dirname):
#     filename = fixture_dirname("gene_models/test_ccds.txt")
#     assert not probe_header(filename, GENE_MODELS_FORMAT_COLUMNS["ccds"])
#     assert probe_columns(filename, GENE_MODELS_FORMAT_COLUMNS["ccds"])

#     filename = fixture_dirname("gene_models/test_ref_flat.txt")
#     assert probe_header(filename, GENE_MODELS_FORMAT_COLUMNS["refflat"])


def test_gene_models_from_known_gene(fixture_dirname):
    filename = fixture_dirname("gene_models/test_known_gene.txt")
    gene_mapping_file = fixture_dirname("gene_models/kg_id2sym.txt.gz")

    assert os.path.exists(filename)

    gene_models = build_gene_models_from_file(
        filename, gene_mapping_file_name=gene_mapping_file,
        file_format="knowngene"
    )
    gene_models.load()
    assert gene_models is not None
    assert len(gene_models.transcript_models) == 20
    assert len(gene_models.gene_models) == 14


def test_gene_models_from_default_ref_gene_2013(fixture_dirname):
    filename = fixture_dirname("gene_models/test_default_ref_gene_201309.txt")
    assert os.path.exists(filename)

    gene_models = build_gene_models_from_file(filename, file_format="default")
    gene_models.load()
    assert gene_models is not None
    assert len(gene_models.transcript_models) == 19
    assert len(gene_models.gene_models) == 19


def test_gene_models_from_default_with_transcript_orig_id(fixture_dirname):
    filename = fixture_dirname(
        "gene_models/test_default_ref_gene_20190220.txt"
    )
    gene_models1 = build_gene_models_from_file(filename, file_format="default")
    gene_models1.load()
    assert gene_models1 is not None
    assert len(gene_models1.transcript_models) == 19
    assert len(gene_models1.gene_models) == 19

    for transcript_model in gene_models1.transcript_models.values():
        assert transcript_model.tr_id != transcript_model.tr_name


@ pytest.mark.parametrize(
    "filename,file_format",
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
def test_load_gene_models_from_file(fixture_dirname, filename, file_format):

    filename = fixture_dirname(filename)
    gene_models = build_gene_models_from_file(
        filename, file_format=file_format)
    gene_models.load()
    assert gene_models is not None


@ pytest.mark.parametrize(
    "filename,file_format,expected",
    [
        ("gene_models/test_ref_flat.txt", None, "refflat"),
        ("gene_models/test_ref_flat_no_header.txt", None, "refflat"),
        ("gene_models/test_ccds.txt", "ccds", "ccds"),
        ("gene_models/test_ref_gene.txt", "refseq", "refseq"),
        ("gene_models/test_ref_seq_hg38.txt", "refseq", "refseq"),
        ("gene_models/test_known_gene.txt", None, "knowngene"),
        ("gene_models/test_default_ref_gene_201309.txt", None, "default"),
        ("gene_models/test_gencode_selenon.gtf", None, "gtf"),
        ("gene_models/test_ref_gene.gtf", None, "gtf"),
        ("gene_models/test_gencode.gtf", None, "gtf"),
    ],
)
def test_infer_gene_models(fixture_dirname, filename, file_format, expected):

    filename = fixture_dirname(filename)
    gene_models = build_gene_models_from_file(
        filename, file_format=file_format)
    with open(filename, encoding="utf8") as infile:
        inferred_file_format = gene_models._infer_gene_model_parser(
            infile, file_format=file_format)

        assert inferred_file_format is not None
        assert inferred_file_format == expected


@pytest.mark.parametrize(
    "filename,file_format",
    [
        ("gene_models/genePred_100.txt.gz", "ucscgenepred"),
        ("gene_models/genePred_453.gtf.gz", "gtf"),
    ],
)
def test_infer_gene_models_no_header(fixture_dirname, filename, file_format):

    filename = fixture_dirname(filename)
    gene_models = build_gene_models_from_file(
        filename, file_format=file_format)
    with gzip.open(filename, "rt") as infile:
        inferred_file_format = gene_models._infer_gene_model_parser(infile)
        assert inferred_file_format is not None
        assert inferred_file_format == file_format


def test_load_ucscgenepred(fixture_dirname):

    filename = fixture_dirname("gene_models/genePred_100.txt.gz")
    gene_models = build_gene_models_from_file(
        filename, file_format="ucscgenepred")
    gene_models.load()

    assert gene_models is not None
    assert "DDX11L1" in gene_models.gene_models


@pytest.mark.parametrize(
    "filename,file_format",
    [
        ("gene_models/genePred_100.txt.gz", "default"),
    ],
)
def test_load_gene_models_no_header(fixture_dirname, filename, file_format):

    filename = fixture_dirname(filename)
    gene_models = build_gene_models_from_file(filename)
    gene_models.load()

    assert gene_models is not None


@pytest.mark.parametrize(
    "filename,file_format",
    [
        ("gene_models/test_ref_flat.txt", "refflat"),
        ("gene_models/test_ref_flat_no_header.txt", "refflat"),
        ("gene_models/test_ccds.txt", "ccds"),
        ("gene_models/test_ref_gene.txt", "refseq"),
        ("gene_models/test_ref_seq_hg38.txt", "refseq"),
        ("gene_models/test_known_gene.txt", "knowngene"),
        ("gene_models/test_default_ref_gene_201309.txt", "default"),
        ("gene_models/test_gencode_selenon.gtf", "gtf"),
        ("gene_models/test_ref_gene.gtf", "gtf"),
        ("gene_models/test_gencode.gtf", "gtf"),
    ],
)
def test_save_load_gene_models_from_file(
    fixture_dirname, filename, file_format, temp_filename
):

    filename = fixture_dirname(filename)
    gene_models = build_gene_models_from_file(
        filename, file_format=file_format)
    gene_models.load()
    assert gene_models is not None
    assert len(gene_models.transcript_models) > 0

    gene_models.save(temp_filename, gzipped=False)

    gene_models1 = build_gene_models_from_file(
        temp_filename, file_format="default")
    gene_models1.load()
    assert gene_models1 is not None

    for tr_id, transcript_model in gene_models.transcript_models.items():
        transcript_model1 = gene_models1.transcript_models[tr_id]

        assert transcript_model.tr_id == transcript_model1.tr_id
        assert transcript_model.tr_name == transcript_model1.tr_name
        assert transcript_model.gene == transcript_model1.gene
        assert transcript_model.chrom == transcript_model1.chrom
        assert transcript_model.cds == transcript_model1.cds
        assert transcript_model.strand == transcript_model1.strand
        assert transcript_model.tx == transcript_model1.tx

        # TODO: THESE DON'T WORK (WITH GTF??)! WHY???
        # assert len(transcript_model.utrs) == len(transcript_model1.utrs)
        # assert transcript_model.utrs == transcript_model1.utrs
        # assert transcript_model.start_codon == transcript_model1.start_codon
        # assert transcript_model.stop_codon == transcript_model1.stop_codon

        assert len(transcript_model.exons) == len(transcript_model1.exons)
        for index, (exon, exon1) in enumerate(zip(
                transcript_model.exons, transcript_model1.exons)):
            assert exon.start == exon1.start, (
                transcript_model.exons[: index + 2],
                transcript_model1.exons[: index + 2],
            )
            assert exon.stop == exon1.stop
            assert exon.frame == exon1.frame
