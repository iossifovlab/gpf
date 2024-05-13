# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme
import pathlib
import textwrap
from contextlib import closing

import pysam

from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    setup_vcf,
)
from dae.tools.vcf_liftover import main


def test_vcf_liftover_simple(
    tmp_path: pathlib.Path,
    liftover_grr_fixture: GenomicResourceRepo,
) -> None:
    vcf_file = setup_vcf(
        tmp_path / "in.vcf.gz", textwrap.dedent("""
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=foo>
##contig=<ID=bar>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1
foo    5   .  A   C   .    .      .    GT     0/0  0/0  0/1
foo    6   .  C   T   .    .      .    GT     0/1  0/0  0/0
foo    7   .  G   A   .    .      .    GT     0/0  1/0  0/1
        """))

    out_vcf = tmp_path / "liftover"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    main(argv, grr=liftover_grr_fixture)

    assert out_vcf.with_suffix(".vcf").exists()

    with closing(pysam.VariantFile(
        str(out_vcf.with_suffix(".vcf")))) as vcffile:

        variants = list(vcffile.fetch())
        assert len(variants) == 3
