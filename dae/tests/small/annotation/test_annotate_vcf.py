# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import pytest
from dae.annotation.annotate_vcf import VCFSource
from dae.genomic_resources.testing import setup_vcf


@pytest.fixture
def sample_vcf(tmp_path: pathlib.Path) -> pathlib.Path:
    filepath = tmp_path / "sample.vcf"
    setup_vcf(filepath, textwrap.dedent("""
        ##fileformat=VCFv4.5
        ##contig=<ID=chr1>
        ##contig=<ID=chr2>
        ##contig=<ID=chr3>
        #CHROM POS ID REF ALT QUAL FILTER INFO
        chr1   10  .  C   T   .    .      .
        chr1   15  .  C   A   .    .      .
        chr2   20  .  C   T   .    .      .
        chr2   25  .  C   A   .    .      .
        chr3   30  .  C   T   .    .      .
        chr3   35  .  C   A   .    .      .
    """))
    return filepath


def test_vcf_source(sample_vcf: pathlib.Path):
    source = VCFSource(sample_vcf)
    variants = list(source.fetch())
    variants_svuids = [fv.summary_variant.svuid for fv in variants]
    assert variants_svuids == [
        "chr1:10.C.T.0",
        "chr1:15.C.A.0",
        "chr2:20.C.T.0",
        "chr2:25.C.A.0",
        "chr3:30.C.T.0",
        "chr3:35.C.A.0",
    ]
