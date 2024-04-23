# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme
import pathlib
import textwrap
from contextlib import closing
from typing import Optional

import pysam
import pytest

from dae.genomic_resources.liftover_chain import (
    build_liftover_chain_from_resource,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    convert_to_tab_separated,
    setup_directories,
    setup_genome,
    setup_gzip,
    setup_vcf,
)
from dae.tools.vcf_liftover import main


@pytest.fixture()
def grr_fixture(
        tmp_path_factory: pytest.TempPathFactory) -> GenomicResourceRepo:
    root_path = tmp_path_factory.mktemp("liftover_tools")
    setup_directories(root_path, {
        "target_genome": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "source_genome": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "liftover_chain": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: liftover_chain

                filename: liftover.chain.gz
            """),
        },
    })
    setup_genome(
        root_path / "target_genome" / "genome.fa",
        textwrap.dedent(f"""
            >chr1
            {25 * 'AGCT'}
            >chr2
            {25 * 'AGCT'}
            """),
    )
    setup_genome(
        root_path / "source_genome" / "genome.fa",
        textwrap.dedent(f"""
            >1
            NNNN{12 * 'AGCT'}NNNN{12 * 'AGCT'}
            >2
            NNNN{12 * 'AGCT'}NNNN{12 * 'AGCT'}
            """),
    )
    setup_gzip(
        root_path / "liftover_chain" / "liftover.chain.gz",
        convert_to_tab_separated("""
        chain||4900||1||48||+||4||52||chr1||48||+||1||49||1
        48 0 0
        0
        chain||4900||1||48||+||55||103||chr1||48||+||48||96||2
        48 0 0
        0
        """),
    )
    return build_filesystem_test_repository(root_path)


@pytest.mark.parametrize("spos, expected", [
    (("1", 4), None),
    (("1", 5), ("chr1", 1, "+", 4900)),
    (("1", 6), ("chr1", 2, "+", 4900)),
    (("1", 7), ("chr1", 3, "+", 4900)),
    (("1", 14), ("chr1", 10, "+", 4900)),
    (("1", 52), ("chr1", 48, "+", 4900)),  # Chain file is kind of broken
    (("1", 53), None),
    (("1", 55), None),
    (("1", 56), ("chr1", 48, "+", 4900)),
    (("1", 80), ("chr1", 72, "+", 4900)),
    (("2", 56), None),
])
def test_liftover_chain_fixture(
        spos: tuple[str, int],
        expected: Optional[tuple[str, int, str, int]],
        grr_fixture: GenomicResourceRepo) -> None:
    res = grr_fixture.get_resource("liftover_chain")
    liftover_chain = build_liftover_chain_from_resource(res)

    assert liftover_chain is not None
    liftover_chain.open()
    chrom, pos = spos
    lo_coordinates = liftover_chain.convert_coordinate(chrom, pos)
    assert lo_coordinates == expected


def test_vcf_liftover_simple(
    tmp_path: pathlib.Path,
    grr_fixture: GenomicResourceRepo,
) -> None:
    vcf_file = setup_vcf(
        tmp_path / "in.vcf.gz", textwrap.dedent("""
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=1>
##contig=<ID=2>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1
1      5   .  A   C   .    .      .    GT     0/0  0/0  0/1
1      6   .  G   T   .    .      .    GT     0/1  0/0  0/0
1      7   .  C   A   .    .      .    GT     0/0  1/0  0/1
        """))

    out_vcf = tmp_path / "liftover"
    argv = [
        "--chain", "liftover_chain",
        "--source-genome", "source_genome",
        "--target-genome", "target_genome",
        "-o", str(out_vcf),
        str(vcf_file),
    ]

    main(argv, grr=grr_fixture)

    assert out_vcf.with_suffix(".vcf").exists()

    with closing(pysam.VariantFile(
        str(out_vcf.with_suffix(".vcf")))) as vcffile:

        variants = list(vcffile.fetch())
        assert len(variants) == 3
