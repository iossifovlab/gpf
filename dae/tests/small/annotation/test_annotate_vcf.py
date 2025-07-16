# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import pytest
from dae.annotation.annotate_vcf import VCFSource
from dae.genomic_resources.testing import setup_pedigree, setup_vcf
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.pedigrees.loader import FamiliesLoader
from dae.testing.acgt_import import acgt_gpf
from dae.variants_loaders.vcf.loader import VcfLoader


@pytest.fixture
def test_gpf_instance(tmp_path: pathlib.Path) -> GPFInstance:
    return acgt_gpf(tmp_path)


@pytest.fixture
def sample_ped(tmp_path: pathlib.Path) -> pathlib.Path:
    filepath = tmp_path / "sample.ped"
    setup_pedigree(filepath, textwrap.dedent("""
        familyId personId dadId momId sex status role
        f1       mom      0     0     2   1      mom
        f1       dad      0     0     1   1      dad
        f1       prb      dad   mom   1   2      prb
    """))
    return filepath


@pytest.fixture
def sample_vcf(tmp_path: pathlib.Path) -> pathlib.Path:
    filepath = tmp_path / "sample.vcf"
    setup_vcf(filepath, textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        ##contig=<ID=chr2>
        ##contig=<ID=chr3>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom dad prb
        chr1   10  .  C   T   .    .      .    GT     0/0 0/0 0/1
        chr2   20  .  C   T   .    .      .    GT     0/1 0/0 0/1
        chr3   30  .  C   T   .    .      .    GT     0/1 0/1 0/1
    """))
    return filepath


def test_vcf_source(
    test_gpf_instance: GPFInstance,
    sample_ped: pathlib.Path,
    sample_vcf: pathlib.Path,
):
    vcf_loader = VcfLoader(
        FamiliesLoader(str(sample_ped)).load(),
        [str(sample_vcf)],
        test_gpf_instance.reference_genome,
    )
    source = VCFSource(vcf_loader)
    result = [
        (full_variant.summary_variant.svuid, len(full_variant.family_variants))
        for full_variant in source.fetch()
    ]
    assert result == [
        ("chr1:10.C.T.1", 1),
        ("chr2:20.C.T.1", 1),
        ("chr3:30.C.T.1", 1),
    ]
