# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest

from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository_factory import (
    GenomicResourceRepo,
)
from dae.genomic_resources.testing import (
    setup_denovo,
    setup_pedigree,
    setup_vcf,
)
from dae.pedigrees.loader import FamiliesLoader
from dae.tools.denovo2vcf import main as denovo2vcf_main
from dae.variants_loaders.vcf.loader import VcfLoader


@pytest.fixture(scope="module")
def trio_pedigree(
    tmp_path_factory: pytest.TempPathFactory,
) -> pathlib.Path:
    root_path = tmp_path_factory.mktemp("test_vcf_serializer_trio_pedigree")
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
    root_path = tmp_path_factory.mktemp("test_vcf_serializer_trio_vcf")

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


@pytest.fixture(scope="module")
def trio_denovo(
    tmp_path_factory: pytest.TempPathFactory,
) -> pathlib.Path:
    root_path = tmp_path_factory.mktemp("test_vcf_serializer_trio_vcf")

    return setup_denovo(root_path / "denovo_data" / "in.tsv", """
chrom  pos  ref  alt person_id
chr1   1    T    G   ch1
chr1   5    T    G   ch1
chr1   12   T    G   ch1
""")

# familyId  location  variant     bestState
# f1         chr1:1    sub(T->G)  2||2||1/0||0||1
# f1         chr1:5    sub(T->G)  2||2||1/0||0||1
# f1         chr1:12   sub(T->G)  2||2||1/0||0||1


def test_denovo2vcf_simple(
    trio_pedigree: pathlib.Path,
    trio_denovo: pathlib.Path,
    tmp_path: pathlib.Path,
    t4c8_grr: GenomicResourceRepo,
) -> None:
    # When:
    denovo2vcf_main(
        [
            str(trio_pedigree),
            str(trio_denovo),
            "--genome", "t4c8_genome",
            "--output", str(tmp_path / "out.vcf"),
        ],
        grr=t4c8_grr,
    )

    # Then:
    assert (tmp_path / "out.vcf").exists()

    genome = build_reference_genome_from_resource(
        t4c8_grr.get_resource("t4c8_genome")).open()
    families = FamiliesLoader(str(trio_pedigree)).load()
    vcf_loader = VcfLoader(
        families,
        [str(tmp_path / "out.vcf")],
        genome,
    )
    variants = list(vcf_loader.family_variants_iterator())
    assert len(variants) == 3


def test_denovo2vcf_stdout(
    trio_pedigree: pathlib.Path,
    trio_denovo: pathlib.Path,
    t4c8_grr: GenomicResourceRepo,
    capfd: pytest.CaptureFixture,
) -> None:
    # When:
    denovo2vcf_main(
        [
            str(trio_pedigree),
            str(trio_denovo),
            "--genome", "t4c8_genome",
        ],
        grr=t4c8_grr,
    )

    # Then:
    captured = capfd.readouterr()
    assert "##source=denovo2vcf" in captured.out
