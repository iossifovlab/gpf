# pylint: disable=W0621,C0114,C0116,W0212,W0613
import gzip
import os
import pathlib
import tempfile
import textwrap
from collections.abc import Callable

import pytest
from dae.genomic_resources.gene_models import (
    GeneModels,
    build_gene_models_from_file,
    build_gene_models_from_resource,
    create_regions_from_genes,
    save_as_default_gene_models,
)
from dae.genomic_resources.gene_models.gene_models import (
    Exon,
    TranscriptModel,
    join_gene_models,
)
from dae.genomic_resources.gene_models.parsing import (
    infer_gene_model_parser,
)
from dae.genomic_resources.testing import (
    build_inmemory_test_resource,
    convert_to_tab_separated,
)
from dae.testing.t4c8_import import t4c8_genes


@pytest.fixture
def fixture_dirname() -> Callable:
    def _fixture_dirname(filename: str) -> str:
        return os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "fixtures",
            filename)

    return _fixture_dirname


@pytest.fixture
def t4c8_gene_models(tmp_path: pathlib.Path) -> GeneModels:
    return t4c8_genes(tmp_path / "gene_models")


def test_gene_models_from_gtf(fixture_dirname: Callable) -> None:
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
def test_gene_models_from_gtf_selenon(
    fixture_dirname: Callable, filename: str,
) -> None:
    gtf_filename = fixture_dirname(filename)
    print(gtf_filename)

    gene_models = build_gene_models_from_file(gtf_filename, file_format="gtf")
    gene_models.load()
    assert gene_models is not None


def test_gene_models_from_ref_gene_ref_seq(fixture_dirname: Callable) -> None:
    filename = fixture_dirname("gene_models/test_ref_gene.txt")
    assert os.path.exists(filename)

    gene_models = build_gene_models_from_file(filename, file_format="refseq")
    gene_models.load()
    assert len(gene_models.transcript_models) == 12
    assert len(gene_models.gene_models) == 12


def test_gene_models_from_ref_seq_orig(fixture_dirname: Callable) -> None:
    filename = fixture_dirname("gene_models/test_ref_seq_hg38.txt")
    assert os.path.exists(filename)

    gene_models = build_gene_models_from_file(filename, file_format="refseq")
    gene_models.load()
    assert gene_models is not None
    assert len(gene_models.transcript_models) == 20
    assert len(gene_models.gene_models) == 8


def test_gene_models_from_gencode(fixture_dirname: Callable) -> None:
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
def test_gene_models_from_ref_flat(
    fixture_dirname: Callable, filename: str,
) -> None:
    filename = fixture_dirname(filename)
    assert os.path.exists(filename)
    gene_models = build_gene_models_from_file(filename, "refflat")
    gene_models.load()
    assert len(gene_models.transcript_models) == 19
    assert len(gene_models.gene_models) == 19


def test_gene_models_from_ccds(fixture_dirname: Callable) -> None:
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


def test_gene_models_from_known_gene(fixture_dirname: Callable) -> None:
    filename = fixture_dirname("gene_models/test_known_gene.txt")
    gene_mapping_file = fixture_dirname("gene_models/kg_id2sym.txt.gz")

    assert os.path.exists(filename)

    gene_models = build_gene_models_from_file(
        filename, gene_mapping_file_name=gene_mapping_file,
        file_format="knowngene",
    )
    gene_models.load()
    assert gene_models is not None
    assert len(gene_models.transcript_models) == 20
    assert len(gene_models.gene_models) == 14


def test_gene_models_from_default_ref_gene_2013(
    fixture_dirname: Callable,
) -> None:
    filename = fixture_dirname("gene_models/test_default_ref_gene_201309.txt")
    assert os.path.exists(filename)

    gene_models = build_gene_models_from_file(filename, file_format="default")
    gene_models.load()
    assert gene_models is not None
    assert len(gene_models.transcript_models) == 19
    assert len(gene_models.gene_models) == 19


def test_gene_models_from_default_with_transcript_orig_id(
    fixture_dirname: Callable,
) -> None:
    filename = fixture_dirname(
        "gene_models/test_default_ref_gene_20190220.txt",
    )
    gene_models1 = build_gene_models_from_file(filename, file_format="default")
    gene_models1.load()
    assert gene_models1 is not None
    assert len(gene_models1.transcript_models) == 19
    assert len(gene_models1.gene_models) == 19

    for transcript_model in gene_models1.transcript_models.values():
        assert transcript_model.tr_id != transcript_model.tr_name


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
    ],


)
def test_load_gene_models_from_file(
    fixture_dirname: Callable, filename: str, file_format: str,
) -> None:

    filename = fixture_dirname(filename)
    gene_models = build_gene_models_from_file(
        filename, file_format=file_format)
    gene_models.load()
    assert gene_models is not None


@pytest.mark.parametrize(
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
def test_infer_gene_models(
    fixture_dirname: Callable,
    filename: str,
    file_format: str | None,
    expected: str,
) -> None:

    filename = fixture_dirname(filename)
    gene_models = build_gene_models_from_file(
        filename, file_format=file_format)
    with open(filename, encoding="utf8") as infile:
        inferred_file_format = infer_gene_model_parser(
            gene_models,
            infile,
            file_format=file_format)

        assert inferred_file_format is not None
        assert inferred_file_format == expected


@pytest.mark.parametrize(
    "filename,file_format",
    [
        ("gene_models/genePred_100.txt.gz", "ucscgenepred"),
        ("gene_models/genePred_453.gtf.gz", "gtf"),
    ],
)
def test_infer_gene_models_no_header(
    fixture_dirname: Callable, filename: str, file_format: str,
) -> None:

    filename = fixture_dirname(filename)
    gene_models = build_gene_models_from_file(
        filename, file_format=file_format)
    with gzip.open(filename, "rt") as infile:
        inferred_file_format = infer_gene_model_parser(gene_models, infile)
        assert inferred_file_format is not None
        assert inferred_file_format == file_format


def test_load_ucscgenepred(fixture_dirname: Callable) -> None:

    filename = fixture_dirname("gene_models/genePred_100.txt.gz")
    gene_models = build_gene_models_from_file(
        filename, file_format="ucscgenepred")
    gene_models.load()

    assert gene_models is not None
    assert "DDX11L1" in gene_models.gene_models


@pytest.mark.parametrize(
    "filename",
    [
        "gene_models/genePred_100.txt.gz",
    ],
)
def test_load_gene_models_no_header(
    fixture_dirname: Callable, filename: str,
) -> None:

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
    fixture_dirname: Callable,
    filename: str,
    file_format: str,
    tmp_path: pathlib.Path,
) -> None:

    filename = fixture_dirname(filename)
    gene_models = build_gene_models_from_file(
        filename, file_format=file_format)
    gene_models.load()
    assert gene_models is not None
    assert len(gene_models.transcript_models) > 0
    temp_filename = str(tmp_path / "gene_models.txt")
    save_as_default_gene_models(gene_models, temp_filename, gzipped=False)

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

        assert len(transcript_model.exons) == len(transcript_model1.exons)
        for index, (exon, exon1) in enumerate(zip(
                transcript_model.exons, transcript_model1.exons, strict=True)):
            assert exon.start == exon1.start, (
                transcript_model.exons[: index + 2],
                transcript_model1.exons[: index + 2],
            )
            assert exon.stop == exon1.stop
            assert exon.frame == exon1.frame


def test_gencode_broken_utrs(
    fixture_dirname: Callable,
) -> None:
    filename = fixture_dirname("gene_models/test_gencode_utr.gtf")
    gene_models = build_gene_models_from_file(filename, "gtf")
    gene_models.load()
    assert gene_models is not None


def test_gencode_example(
    fixture_dirname: Callable,
) -> None:
    filename = fixture_dirname("gene_models/example_gencode.txt")
    gene_models = build_gene_models_from_file(filename, "gtf")
    gene_models.load()
    assert gene_models is not None
    assert len(gene_models.gene_models) == 1
    assert len(gene_models.transcript_models) == 1
    assert "C2CD4C" in gene_models.gene_models

    assert "ENST00000332235.7" in gene_models.transcript_models
    tm = gene_models.transcript_models["ENST00000332235.7"]

    assert tm.tr_id == "ENST00000332235.7"
    assert tm.cds == (407096, 408361)
    assert tm.tx == (405438, 409170)
    assert len(tm.exons) == 2
    assert tm.strand == "-"


def test_gencode_example2() -> None:
    # Example from: https://www.gencodegenes.org/pages/data_format.html
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: gencode.txt, format: gtf}",
            "gencode.txt": convert_to_tab_separated(textwrap.dedent("""
chr19  HAVANA  gene         405438  409170  .  -  .  gene_id||"ENSG00000183186.7";gene_type||"protein_coding";gene_name||"C2CD4C";level||2;havana_gene||"OTTHUMG00000180534.3";
chr19  HAVANA  transcript   405438  409170  .  -  .  gene_id||"ENSG00000183186.7";transcript_id||"ENST00000332235.7";||gene_type||"protein_coding";||gene_name||"C2CD4C";||transcript_type||"protein_coding";||transcript_name||"C2CD4C-001";||level||2;||protein_id||"ENSP00000328677.4";||transcript_support_level||"2";||tag||"basic";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS45890.1";||havana_gene||"OTTHUMG00000180534.3";||havana_transcript||"OTTHUMT00000451789.3";
chr19  HAVANA  exon         409006  409170  .  -  .  gene_id||"ENSG00000183186.7";transcript_id||"ENST00000332235.7";||gene_type||"protein_coding";||gene_name||"C2CD4C";||transcript_type||"protein_coding";||transcript_name||"C2CD4C-001";||exon_number||1;||exon_id||"ENSE00001322986.5";||level||2;protein_id||"ENSP00000328677.4";transcript_support_level||"2";tag||"basic";tag||"appris_principal_1";tag||"CCDS";ccdsid||"CCDS45890.1";havana_gene||"OTTHUMG00000180534.3";havana_transcript||"OTTHUMT00000451789.3";
chr19  HAVANA  exon         405438  408401  .  -  .  gene_id||"ENSG00000183186.7";transcript_id||"ENST00000332235.7";||gene_type||"protein_coding";||gene_name||"C2CD4C";||transcript_type||"protein_coding";||transcript_name||"C2CD4C-001";||exon_number||2;||exon_id||"ENSE00001290344.6";||level||2;protein_id||"ENSP00000328677.4";transcript_support_level||"2";tag||"basic";tag||"appris_principal_1";tag||"CCDS";ccdsid||"CCDS45890.1";havana_gene||"OTTHUMG00000180534.3";havana_transcript||"OTTHUMT00000451789.3";
chr19  HAVANA  CDS          407099  408361  .  -  0  gene_id||"ENSG00000183186.7";transcript_id||"ENST00000332235.7";||gene_type||"protein_coding";||gene_name||"C2CD4C";||transcript_type||"protein_coding";||transcript_name||"C2CD4C-001";||exon_number||2;||exon_id||"ENSE00001290344.6";||level||2;protein_id||"ENSP00000328677.4";transcript_support_level||"2";tag||"basic";tag||"appris_principal_1";tag||"CCDS";ccdsid||"CCDS45890.1";havana_gene||"OTTHUMG00000180534.3";havana_transcript||"OTTHUMT00000451789.3";
chr19  HAVANA  start_codon  408359  408361  .  -  0  gene_id||"ENSG00000183186.7";transcript_id||"ENST00000332235.7";||gene_type||"protein_coding";||gene_name||"C2CD4C";||transcript_type||"protein_coding";||transcript_name||"C2CD4C-001";||exon_number||2;||exon_id||"ENSE00001290344.6";||level||2;protein_id||"ENSP00000328677.4";transcript_support_level||"2";tag||"basic";tag||"appris_principal_1";tag||"CCDS";ccdsid||"CCDS45890.1";havana_gene||"OTTHUMG00000180534.3";havana_transcript||"OTTHUMT00000451789.3";
chr19  HAVANA  stop_codon   407096  407098  .  -  0  gene_id||"ENSG00000183186.7";transcript_id||"ENST00000332235.7";||gene_type||"protein_coding";||gene_name||"C2CD4C";||transcript_type||"protein_coding";||transcript_name||"C2CD4C-001";||exon_number||2;||exon_id||"ENSE00001290344.6";||level||2;protein_id||"ENSP00000328677.4";transcript_support_level||"2";tag||"basic";tag||"appris_principal_1";tag||"CCDS";ccdsid||"CCDS45890.1";havana_gene||"OTTHUMG00000180534.3";havana_transcript||"OTTHUMT00000451789.3";
chr19  HAVANA  UTR          409006  409170  .  -  .  gene_id||"ENSG00000183186.7";transcript_id||"ENST00000332235.7";||gene_type||"protein_coding";||gene_name||"C2CD4C";||transcript_type||"protein_coding";||transcript_name||"C2CD4C-001";||exon_number||1;||exon_id||"ENSE00001322986.5";||level||2;protein_id||"ENSP00000328677.4";transcript_support_level||"2";tag||"basic";tag||"appris_principal_1";tag||"CCDS";ccdsid||"CCDS45890.1";havana_gene||"OTTHUMG00000180534.3";havana_transcript||"OTTHUMT00000451789.3";
chr19  HAVANA  UTR          405438  407098  .  -  .  gene_id||"ENSG00000183186.7";transcript_id||"ENST00000332235.7";||gene_type||"protein_coding";||gene_name||"C2CD4C";||transcript_type||"protein_coding";||transcript_name||"C2CD4C-001";||exon_number||2;||exon_id||"ENSE00001290344.6";||level||2;protein_id||"ENSP00000328677.4";transcript_support_level||"2";tag||"basic";tag||"appris_principal_1";tag||"CCDS";ccdsid||"CCDS45890.1";havana_gene||"OTTHUMG00000180534.3";havana_transcript||"OTTHUMT00000451789.3";
chr19  HAVANA  UTR          408362  408401  .  -  .  gene_id||"ENSG00000183186.7";transcript_id||"ENST00000332235.7";||gene_type||"protein_coding";||gene_name||"C2CD4C";||transcript_type||"protein_coding";||transcript_name||"C2CD4C-001";||exon_number||2;||exon_id||"ENSE00001290344.6";||level||2;protein_id||"ENSP00000328677.4";transcript_support_level||"2";tag||"basic";tag||"appris_principal_1";tag||"CCDS";ccdsid||"CCDS45890.1";havana_gene||"OTTHUMG00000180534.3";havana_transcript||"OTTHUMT00000451789.3";
""")),  # noqa: E501
        })

    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    assert len(gene_models.gene_models) == 1
    assert len(gene_models.transcript_models) == 1
    assert "C2CD4C" in gene_models.gene_models

    assert "ENST00000332235.7" in gene_models.transcript_models
    tm = gene_models.transcript_models["ENST00000332235.7"]

    assert tm.tr_id == "ENST00000332235.7"
    assert tm.cds == (407096, 408361)
    assert tm.tx == (405438, 409170)
    assert len(tm.exons) == 2
    assert tm.strand == "-"


def test_ensembl_example() -> None:
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: gencode.txt, format: gtf}",
            "gencode.txt": convert_to_tab_separated(textwrap.dedent("""
#!genome-build GRCh38
11  ensembl_havana  gene        5422111  5423206  .  +  .  gene_id||"ENSG00000167360";gene_version||"4";gene_name||"OR51Q1";gene_source||"ensembl_havana";gene_biotype||"protein_coding";
11  ensembl_havana  transcript  5422111  5423206  .  +  .  gene_id||"ENSG00000167360";gene_version||"4";transcript_id||"ENST00000300778";transcript_version||"4";gene_name||"OR51Q1";gene_source||"ensembl_havana";gene_biotype||"protein_coding";transcript_name||"OR51Q1-001";transcript_source||"ensembl_havana";transcript_biotype||"protein_coding";tag||"CCDS";ccds_id||"CCDS31381";
11  ensembl_havana  exon        5422111  5423206  .  +  .  gene_id||"ENSG00000167360";gene_version||"4";transcript_id||"ENST00000300778";transcript_version||"4";exon_number||"1";gene_name||"OR51Q1";gene_source||"ensembl_havana";gene_biotype||"protein_coding";transcript_name||"OR51Q1-001";transcript_source||"ensembl_havana";transcript_biotype||"protein_coding";tag||"CCDS";ccds_id||"CCDS31381";exon_id||"ENSE00001276439";exon_version||"4";
11  ensembl_havana  CDS         5422201  5423151  .  +  0  gene_id||"ENSG00000167360";gene_version||"4";transcript_id||"ENST00000300778";transcript_version||"4";exon_number||"1";gene_name||"OR51Q1";gene_source||"ensembl_havana";gene_biotype||"protein_coding";transcript_name||"OR51Q1-001";transcript_source||"ensembl_havana";transcript_biotype||"protein_coding";tag||"CCDS";ccds_id||"CCDS31381";protein_id||"ENSP00000300778";protein_version||"4";
11  ensembl_havana  start_codon 5422201  5422203  .  +  0  gene_id||"ENSG00000167360";gene_version||"4";transcript_id||"ENST00000300778";transcript_version||"4";exon_number||"1";gene_name||"OR51Q1";gene_source||"ensembl_havana";gene_biotype||"protein_coding";transcript_name||"OR51Q1-001";transcript_source||"ensembl_havana";transcript_biotype||"protein_coding";tag||"CCDS";ccds_id||"CCDS31381";
11  ensembl_havana  stop_codon  5423152  5423154  .  +  0  gene_id||"ENSG00000167360";gene_version||"4";transcript_id||"ENST00000300778";transcript_version||"4";exon_number||"1";gene_name||"OR51Q1";gene_source||"ensembl_havana";gene_biotype||"protein_coding";transcript_name||"OR51Q1-001";transcript_source||"ensembl_havana";transcript_biotype||"protein_coding";tag||"CCDS";ccds_id||"CCDS31381";
11  ensembl_havana  UTR         5422111  5422200  .  +  .  gene_id||"ENSG00000167360";gene_version||"4";transcript_id||"ENST00000300778";transcript_version||"4";gene_name||"OR51Q1";gene_source||"ensembl_havana";gene_biotype||"protein_coding";transcript_name||"OR51Q1-001";transcript_source||"ensembl_havana";transcript_biotype||"protein_coding";tag||"CCDS";ccds_id||"CCDS31381";
11  ensembl_havana  UTR         5423155  5423206  .  +  .  gene_id||"ENSG00000167360";gene_version||"4";transcript_id||"ENST00000300778";transcript_version||"4";gene_name||"OR51Q1";gene_source||"ensembl_havana";gene_biotype||"protein_coding";transcript_name||"OR51Q1-001";transcript_source||"ensembl_havana";transcript_biotype||"protein_coding";tag||"CCDS";ccds_id||"CCDS31381";tag||"a||b||c";
""")),  # noqa: E501
        })
    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    assert len(gene_models.gene_models) == 1
    assert len(gene_models.transcript_models) == 1
    assert "OR51Q1" in gene_models.gene_models

    assert "ENST00000300778" in gene_models.transcript_models
    tm = gene_models.transcript_models["ENST00000300778"]

    assert tm.tr_id == "ENST00000300778"
    assert tm.cds == (5422201, 5423154)
    assert tm.tx == (5422111, 5423206)
    assert len(tm.exons) == 1
    assert tm.strand == "+"


@pytest.mark.parametrize(
    "gene,expected", [
        ("t4", "chr1:5-85"),
        ("c8", "chr1:100-205"),
    ],
)
def test_create_regions_from_genes(
    t4c8_gene_models: GeneModels,
    gene: str,
    expected: str,
) -> None:
    genes = [gene]
    regions = None
    result = create_regions_from_genes(
        t4c8_gene_models, genes, regions,
        gene_regions_heuristic_extend=0,
    )
    assert result is not None
    assert len(result) == 1
    reg = result[0]
    assert str(reg) == expected


def test_invalid_cds():
    transcript = TranscriptModel(
        gene="gene",
        tr_id="transcript",
        tr_name="transcript",
        chrom="chr",
        strand="+",
        exons=[Exon(start=100, stop=200)],
        cds=(300, 200),  # Invalid CDS range
        tx=(100, 200),
    )
    cds_regions = transcript.cds_regions()
    assert not cds_regions

    utr3_regions = transcript.utr3_regions()
    assert not utr3_regions

    utr5_regions = transcript.utr5_regions()
    assert not utr5_regions


@pytest.fixture(scope="module")
def transcript_with_utrs():
    return TranscriptModel(
        gene="gene",
        tr_id="transcript",
        tr_name="transcript",
        chrom="chr",
        strand="+",
        exons=[
            Exon(start=0, stop=1),  # UTR5 (2 bp)
            Exon(start=2, stop=5),  # CDS (4 bp)
            Exon(start=6, stop=9),  # UTR3 (4 bp)
        ],
        cds=(2, 5),
        tx=(0, 9),
    )


def test_total_len_with_utrs(transcript_with_utrs):
    assert transcript_with_utrs.total_len() == 10


def test_cds_len_with_utrs(transcript_with_utrs):
    assert transcript_with_utrs.cds_len() == 4


def test_utr5_len_with_utrs(transcript_with_utrs):
    assert transcript_with_utrs.utr5_len() == 2


def test_utr3_len_with_utrs(transcript_with_utrs):
    assert transcript_with_utrs.utr3_len() == 4


@pytest.fixture
def transcript_with_matching_frames():
    return TranscriptModel(
        gene="gene",
        tr_id="transcript",
        tr_name="transcript",
        chrom="chr",
        strand="+",
        exons=[
            Exon(start=0, stop=2, frame=0),
            Exon(start=3, stop=5, frame=0),
            Exon(start=6, stop=8, frame=0),
        ],
        cds=(0, 8),
        tx=(0, 8),
    )


def test_test_frames_true(transcript_with_matching_frames):
    assert transcript_with_matching_frames.test_frames() is True


def test_test_frames_false(transcript_with_matching_frames):
    transcript_with_matching_frames.exons[1].frame = 1
    assert transcript_with_matching_frames.test_frames() is False


def test_get_exon_number_for_out_of_bounds():
    transcript = TranscriptModel(
        gene="gene",
        tr_id="transcript",
        tr_name="transcript",
        chrom="chr",
        strand="+",
        exons=[
            Exon(start=0, stop=10),
            Exon(start=20, stop=30),
        ],
        cds=(0, 30),
        tx=(0, 30),
    )

    result = transcript.get_exon_number_for(start=100, stop=110)
    assert result == 0


def test_join_gene_models_invalid_count(fixture_dirname):
    filename = fixture_dirname("gene_models/example_gencode.txt")
    gene_models = build_gene_models_from_file(filename, "gtf")
    gene_models.load()

    with pytest.raises(ValueError, match="at least 2 arguments"):
        join_gene_models(gene_models)


def test_join_gene_models(
    fixture_dirname,
    t4c8_gene_models: GeneModels,
) -> None:
    filename = fixture_dirname("gene_models/example_gencode.txt")
    example_gencode = build_gene_models_from_file(filename, "gtf")
    example_gencode.load()
    assert example_gencode.gene_names() == ["C2CD4C"]
    assert len(example_gencode.transcript_models) == 1

    t4c8_gene_models.load()
    assert t4c8_gene_models.gene_names() == ["t4", "c8"]
    assert len(t4c8_gene_models.transcript_models) == 2

    combined = join_gene_models(example_gencode, t4c8_gene_models)
    assert combined.gene_names() == ["C2CD4C", "t4", "c8"]
    assert len(combined.transcript_models) == 3


def test_relabel_chromosomes(fixture_dirname) -> None:
    filename = fixture_dirname("gene_models/example_gencode.txt")
    gene_model = build_gene_models_from_file(filename, "gtf")
    gene_model.load()

    transcript_id = "ENST00000332235.7"

    assert gene_model.transcript_models[transcript_id].chrom == "chr19"
    assert "chr19" in gene_model.utr_models

    gene_model.relabel_chromosomes(relabel={"chr19": "19"})

    assert gene_model.transcript_models[transcript_id].chrom == "19"
    assert "chr19" not in gene_model.utr_models
    assert "19" in gene_model.utr_models


def test_relabel_chromosomes_from_mapfile(fixture_dirname) -> None:
    filename = fixture_dirname("gene_models/example_gencode.txt")
    gene_model = build_gene_models_from_file(filename, "gtf")
    gene_model.load()

    transcript_id = "ENST00000332235.7"
    assert gene_model.transcript_models[transcript_id].chrom == "chr19"
    assert "chr19" in gene_model.utr_models

    with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
        tmp.write("chr19 19")
        tmp_path = tmp.name

    gene_model.relabel_chromosomes(map_file=tmp_path)

    assert gene_model.transcript_models[transcript_id].chrom == "19"
    assert "chr19" not in gene_model.utr_models
    assert "19" in gene_model.utr_models


def test_is_loaded(fixture_dirname) -> None:
    filename = fixture_dirname("gene_models/example_gencode.txt")
    gene_model = build_gene_models_from_file(filename, "gtf")
    assert gene_model.is_loaded() is False

    gene_model.load()
    assert gene_model.is_loaded() is True


def test_gene_models_by_location(fixture_dirname) -> None:
    filename = fixture_dirname("gene_models/test_ccds.txt")
    gene_model = build_gene_models_from_file(filename, "ccds")
    gene_model.load()

    results = gene_model.gene_models_by_location("chr1", 69091)
    assert len(results) == 1
    assert results[0].tr_id == "CCDS30547.1_1"

    results = gene_model.gene_models_by_location("chr1", 0, 500000)
    assert len(results) == 2
    assert results[0].tr_id == "CCDS30547.1_1"
    assert results[1].tr_id == "CCDS41220.1_1"

    results = gene_model.gene_models_by_location("chr1", 500000, 0)
    assert len(results) == 2
    assert results[0].tr_id == "CCDS30547.1_1"
    assert results[1].tr_id == "CCDS41220.1_1"


def test_all_regions(fixture_dirname) -> None:
    filename = fixture_dirname("gene_models/example_gencode.txt")
    gene_model = build_gene_models_from_file(filename, "gtf")
    gene_model.load()

    transcript = gene_model.transcript_models["ENST00000332235.7"]
    regions = transcript.all_regions()
    assert len(regions) == 2

    assert regions[0].chrom == "chr19"
    assert regions[0].start == 405438
    assert regions[0].stop == 408401

    assert regions[1].chrom == "chr19"
    assert regions[1].start == 409006
    assert regions[1].stop == 409170


def test_all_regions_ss_extend() -> None:
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: gene_model.txt}",
            "gene_model.txt": convert_to_tab_separated(textwrap.dedent("""
chr	trID	gene	strand	tsBeg	txEnd	cdsStart	cdsEnd	exonStarts	exonEnds	exonFrames	atts
1	transcript_1	gene_1	+	100	350	160	300	100,145,210,245,315	150,205,250,310,350	0,0,0,0,0	bin:1;cdsStartStat:cmpl;cdsEndStat:cmpl;exonCount:5;score:0
""")),  # noqa: E501
        })
    gene_models = build_gene_models_from_resource(res)
    gene_models.load()

    transcript = gene_models.transcript_models["transcript_1"]
    regions = transcript.all_regions(ss_extend=5)

    assert len(regions) == 5

    assert regions[0].chrom == "1"
    assert regions[0].start == 100
    assert regions[0].stop == 150

    assert regions[1].chrom == "1"
    assert regions[1].start == 145
    assert regions[1].stop == 205 + 5

    assert regions[2].chrom == "1"
    assert regions[2].start == 210 - 5
    assert regions[2].stop == 250 + 5

    assert regions[3].chrom == "1"
    assert regions[3].start == 245 - 5
    assert regions[3].stop == 310

    assert regions[4].chrom == "1"
    assert regions[4].start == 315
    assert regions[4].stop == 350
