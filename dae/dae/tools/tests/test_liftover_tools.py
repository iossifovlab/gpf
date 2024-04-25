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
    #
    # The initial header line starts with the keyword chain, followed
    # by 11 required attribute values, and ends with a blank line.
    #
    # The attributes include:
    #
    # score -- chain score
    # tName -- chromosome (reference/target sequence); source contig;
    # tSize -- chromosome size (reference/target sequence); full length of the
    #          source chromosome;
    # tStrand -- strand (reference/target sequence); must be +
    # tStart -- alignment start position (reference/target sequence);
    #           Start of source region
    # tEnd -- alignment end position (reference/target sequence);
    #         End of source region
    # qName -- chromosome (query sequence); target chromosome name;
    # qSize -- chromosome size (query sequence); Full length of the chromosome
    # qStrand -- strand (query sequence); + or -
    # qStart -- alignment start position (query sequence); target start;
    # qEnd -- alignment end position (query sequence); target end;
    # id -- chain ID
    #
    # Block format:
    # Alignment data lines contain three required attribute values:

    # size dt dq
    # size -- the size of the ungapped alignment
    # dt -- the difference between the end of this block and the beginning
    #       of the next block (reference/target sequence)
    # dq -- the difference between the end of this block and the beginning
    #       of the next block (query sequence)
    #
    # The last line of the alignment section contains only one number: the
    # ungapped alignment size of the last block.
    #
    setup_gzip(
        root_path / "liftover_chain" / "liftover.chain.gz",
        convert_to_tab_separated("""
        chain 4900 foo 104 + 4 104 chrFoo 100 + 0 96 1
        48 4 0
        48 0 0
        0
        """),
    )
    setup_genome(
        root_path / "target_genome" / "genome.fa",
        textwrap.dedent(f"""
            >chrFoo
            {25 * 'ACGT'}
            >chrBar
            {25 * 'ACGT'}
            >chrBaz
            {25 * 'ACGT'}
            """),
    )
    setup_genome(
        root_path / "source_genome" / "genome.fa",
        textwrap.dedent(f"""
            >foo
            NNNN{12 * 'ACGT'}NNNN{12 * 'ACGT'}
            >bar
            NNNN{12 * 'ACGT'}NNNNNN{12 * 'ACGT'}
            >baz
            NNNN{12 * 'TGCA'}NNNNNNNN{12 * 'TGCA'}
            """),
    )

    return build_filesystem_test_repository(root_path)


@pytest.mark.parametrize("schrom, spos, expected", [
    ("foo", 3, None),
    ("foo", 4, None),
    ("foo", 5, ("chrFoo", 1, "+", 4900)),
    ("foo", 6, ("chrFoo", 2, "+", 4900)),
    ("foo", 7, ("chrFoo", 3, "+", 4900)),
    ("foo", 14, ("chrFoo", 10, "+", 4900)),
    ("foo", 51, ("chrFoo", 47, "+", 4900)),
    ("foo", 52, ("chrFoo", 48, "+", 4900)),
    ("foo", 53, None),
    ("foo", 54, None),
    ("foo", 55, None),
    ("foo", 56, None),
    ("foo", 57, ("chrFoo", 49, "+", 4900)),
    ("foo", 58, ("chrFoo", 50, "+", 4900)),
    ("foo", 80, ("chrFoo", 72, "+", 4900)),
    ("foo", 103, ("chrFoo", 95, "+", 4900)),
    ("foo", 104, ("chrFoo", 96, "+", 4900)),
    ("foo", 105, None),
    ("bar", 5, None),
])
def test_liftover_chain_fixture(
        schrom: str,
        spos: int,
        expected: Optional[tuple[str, int, str, int]],
        grr_fixture: GenomicResourceRepo) -> None:
    res = grr_fixture.get_resource("liftover_chain")
    liftover_chain = build_liftover_chain_from_resource(res)

    assert liftover_chain is not None
    liftover_chain.open()
    lo_coordinates = liftover_chain.convert_coordinate(schrom, spos)
    assert lo_coordinates == expected


def test_vcf_liftover_simple(
    tmp_path: pathlib.Path,
    grr_fixture: GenomicResourceRepo,
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

    main(argv, grr=grr_fixture)

    assert out_vcf.with_suffix(".vcf").exists()

    with closing(pysam.VariantFile(
        str(out_vcf.with_suffix(".vcf")))) as vcffile:

        variants = list(vcffile.fetch())
        assert len(variants) == 3
