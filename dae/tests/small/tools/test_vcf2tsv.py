# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest

from dae.genomic_resources.repository_factory import (
    GenomicResourceRepo,
)
from dae.genomic_resources.testing import (
    setup_pedigree,
    setup_vcf,
)
from dae.tools.vcf2tsv import main as vcf2tsv_main


@pytest.fixture(scope="module")
def trio_pedigree(
    tmp_path_factory: pytest.TempPathFactory,
) -> pathlib.Path:
    root_path = tmp_path_factory.mktemp("test_vcf2tsv")
    return setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f1		    mom1		0	    0	    2	1	    mom
    f1		    dad1		0	    0	    1	1	    dad
    f1		    ch1		    dad1	mom1	2	2	    prb
    """)


@pytest.fixture(scope="module")
def trio_vcf(
    tmp_path_factory: pytest.TempPathFactory,
) -> pathlib.Path:
    root_path = tmp_path_factory.mktemp("test_vcf2tsv")

    return setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=INH,Number=1,Type=String,Description="Inheritance">
    ##contig=<ID=chr1>
    #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1
    chr1   1   .  T   G   .    .      .    GT     0/0  0/0  0/1
    chr1   5   .  T   G   .    .      .    GT     0/0  0/0  0/1
    chr1   12  .  T   G   .    .      .    GT     0/0  0/0  0/1
    """)


def test_vcf2tsv_simple(
    trio_pedigree: pathlib.Path,
    trio_vcf: pathlib.Path,
    tmp_path: pathlib.Path,
    t4c8_grr: GenomicResourceRepo,
) -> None:
    # When:
    vcf2tsv_main(
        [
            str(trio_pedigree),
            str(trio_vcf),
            "--output", str(tmp_path / "out.tsv"),
            "--genome", "t4c8_genome",
            "--vcf-denovo-mode", "denovo",
            "--vcf-omission-mode", "omission",
        ],
        grr=t4c8_grr,
    )

    # Then:
    assert (tmp_path / "out.tsv").exists()
    assert len((tmp_path / "out.tsv").read_text().splitlines()) == 4
