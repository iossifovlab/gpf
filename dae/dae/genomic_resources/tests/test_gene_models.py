import pytest

import os

from dae.genomic_resources.gene_models import load_gene_models
from dae.genomic_resources.gene_models import _open_file


def test_gene_models_from_gtf(fixture_dirname):
    gtf_filename = fixture_dirname("gene_models/test_ref_gene.gtf")
    print(gtf_filename)

    assert os.path.exists(gtf_filename)

    gm = load_gene_models(gtf_filename, fileformat="gtf")
    assert gm is not None
    assert len(gm.transcript_models) == 12
    assert len(gm.gene_models) == 12


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

    gm = load_gene_models(gtf_filename, fileformat="gtf")
    assert gm is not None


def test_gene_models_from_ref_gene_ref_seq(fixture_dirname):
    filename = fixture_dirname("gene_models/test_ref_gene.txt")
    assert os.path.exists(filename)

    gm = load_gene_models(filename, fileformat="refseq")
    assert len(gm.transcript_models) == 12
    assert len(gm.gene_models) == 12


def test_gene_models_from_ref_seq_orig(fixture_dirname):
    filename = fixture_dirname("gene_models/test_ref_seq_hg38.txt")
    assert os.path.exists(filename)

    gm = load_gene_models(filename, fileformat="refseq")
    assert gm is not None
    assert len(gm.transcript_models) == 20
    assert len(gm.gene_models) == 8


def test_gene_models_from_gencode(fixture_dirname):
    filename = fixture_dirname("gene_models/test_gencode.gtf")
    assert os.path.exists(filename)
    gm = load_gene_models(filename, "gtf")
    assert len(gm.transcript_models) == 19
    assert len(gm.gene_models) == 10


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
    gm = load_gene_models(filename, "refflat")
    assert len(gm.transcript_models) == 19
    assert len(gm.gene_models) == 19


def test_gene_models_from_ccds(fixture_dirname):
    filename = fixture_dirname("gene_models/test_ccds.txt")
    gene_mapping_file = fixture_dirname("gene_models/ccds_id2sym.txt.gz")

    assert os.path.exists(filename)

    gm = load_gene_models(
        filename, fileformat="ccds", gene_mapping_filename=gene_mapping_file)
    assert len(gm.transcript_models) == 20
    assert len(gm.gene_models) == 15

    assert gm is not None
    assert len(gm.transcript_models) == 20
    assert len(gm.gene_models) == 15


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

    gm = load_gene_models(
        filename, gene_mapping_filename=gene_mapping_file,
        fileformat="knowngene"
    )
    assert gm is not None
    assert len(gm.transcript_models) == 20
    assert len(gm.gene_models) == 14


def test_gene_models_from_default_ref_gene_2013(fixture_dirname):
    filename = fixture_dirname("gene_models/test_default_ref_gene_201309.txt")
    assert os.path.exists(filename)

    gm = load_gene_models(filename, fileformat="default")
    assert gm is not None
    assert len(gm.transcript_models) == 19
    assert len(gm.gene_models) == 19


def test_gene_models_from_default_with_transcript_orig_id(fixture_dirname):
    filename = fixture_dirname(
        "gene_models/test_default_ref_gene_20190220.txt"
    )
    gm1 = load_gene_models(filename, fileformat="default")
    assert gm1 is not None
    assert len(gm1.transcript_models) == 19
    assert len(gm1.gene_models) == 19

    for tm in gm1.transcript_models.values():
        assert tm.tr_id != tm.tr_name


@ pytest.mark.parametrize(
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


@ pytest.mark.parametrize(
    "filename,fileformat,expected",
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
def test_infer_gene_models(fixture_dirname, filename, fileformat, expected):

    filename = fixture_dirname(filename)
    with _open_file(filename) as infile:
        gm = load_gene_models(filename, fileformat=fileformat)
        inferred_fileformat = gm._infer_gene_model_parser(
            infile, fileformat=fileformat)

        assert inferred_fileformat is not None
        assert inferred_fileformat == expected


@ pytest.mark.parametrize(
    "filename,fileformat",
    [
        ("gene_models/genePred_100.txt.gz", "ucscgenepred"),
        ("gene_models/genePred_453.gtf.gz", "gtf"),
    ],
)
def test_infer_gene_models_no_header(fixture_dirname, filename, fileformat):

    filename = fixture_dirname(filename)
    with _open_file(filename) as infile:
        gm = load_gene_models(filename, fileformat=fileformat)
        inferred_fileformat = gm._infer_gene_model_parser(infile)
        assert inferred_fileformat is not None
        assert inferred_fileformat == fileformat


def test_load_ucscgenepred(fixture_dirname):

    filename = fixture_dirname("gene_models/genePred_100.txt.gz")
    gm = load_gene_models(filename, fileformat="ucscgenepred")
    assert gm is not None
    assert "DDX11L1" in gm.gene_models


@pytest.mark.parametrize(
    "filename,fileformat",
    [
        ("gene_models/genePred_100.txt.gz", "default"),
    ],
)
def test_load_gene_models_no_header(fixture_dirname, filename, fileformat):

    filename = fixture_dirname(filename)
    gm = load_gene_models(filename)
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
        ("gene_models/test_gencode_selenon.gtf", "gtf"),
        ("gene_models/test_ref_gene.gtf", "gtf"),
        ("gene_models/test_gencode.gtf", "gtf"),
    ],
)
def test_save_load_gene_models(
    fixture_dirname, filename, fileformat, temp_filename
):

    filename = fixture_dirname(filename)
    gm = load_gene_models(filename, fileformat=fileformat)
    assert gm is not None
    assert len(gm.transcript_models) > 0

    gm.save(temp_filename, gzipped=False)

    gm1 = load_gene_models(temp_filename, fileformat="default")
    assert gm1 is not None

    for tr_id, tm in gm.transcript_models.items():
        tm1 = gm1.transcript_models[tr_id]

        assert tm.tr_id == tm1.tr_id
        assert tm.tr_name == tm1.tr_name
        assert tm.gene == tm1.gene
        assert tm.chrom == tm1.chrom
        assert tm.cds == tm1.cds
        assert tm.strand == tm1.strand
        assert tm.tx == tm1.tx

        # TODO: THESE DON'T WORK (WITH GTF??)! WHY???
        # assert len(tm.utrs) == len(tm1.utrs)
        # assert tm.utrs == tm1.utrs
        # assert tm.start_codon == tm1.start_codon
        # assert tm.stop_codon == tm1.stop_codon

        assert len(tm.exons) == len(tm1.exons)
        for index, (exon, exon1) in enumerate(zip(tm.exons, tm1.exons)):
            assert exon.start == exon1.start, (
                tm.exons[: index + 2],
                tm1.exons[: index + 2],
            )
            assert exon.stop == exon1.stop
            assert exon.frame == exon1.frame


@pytest.mark.skip
def test_mouse_gene_models():
    dirname = "/home/lubo/Work/seq-pipeline/gpf_validation_data/" \
        "mouse/mouseStrains/mouse"
    filename = "mouse.GRCm38.gtf.gz"

    gm = load_gene_models(os.path.join(dirname, filename), fileformat="gtf")
    assert gm is not None
