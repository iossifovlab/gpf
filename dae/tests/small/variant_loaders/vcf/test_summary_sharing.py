# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import textwrap

import pytest
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.testing import (
    build_filesystem_test_resource,
    setup_directories,
)
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.testing import (
    setup_genome,
    setup_pedigree,
    setup_vcf,
)
from dae.utils.regions import Region
from dae.variants_loaders.vcf.loader import VcfLoader


@pytest.fixture(scope="module")
def genome(tmp_path_factory: pytest.TempPathFactory) -> ReferenceGenome:
    root_path = tmp_path_factory.mktemp("genome")
    setup_genome(
        root_path / "chr.fa",
        f"""
        >1
        {25 * "ACGT"}
        """,
    )

    setup_directories(root_path, {
        GR_CONF_FILE_NAME: """
            type: genome
            filename: chr.fa
        """,
    })
    res = build_filesystem_test_resource(root_path)
    return build_reference_genome_from_resource(res)


@pytest.fixture(scope="module")
def two_families_ped(tmp_path_factory: pytest.TempPathFactory) -> FamiliesData:
    root_path = tmp_path_factory.mktemp("quads_f1_ped")
    ped_path = setup_pedigree(
        root_path / "quads_f1.ped",
        textwrap.dedent("""
        familyId personId dadId momId sex status role
        f1       mom1     0     0     2   1      mom
        f1       dad1     0     0     1   1      dad
        f1       prb1     dad1  mom1  1   2      prb
        f2       mom2     0     0     2   1      mom
        f2       dad2     0     0     1   1      dad
        f2       prb2     dad2  mom2  1   2      prb
        """))

    return FamiliesLoader(ped_path).load()


@pytest.fixture(scope="module")
def two_families_vcf(
    tmp_path_factory: pytest.TempPathFactory,
    two_families_ped: FamiliesData,
    genome: ReferenceGenome,
) -> VcfLoader:
    root_path = tmp_path_factory.mktemp("quads_f1_chr1")
    vcf_path = setup_vcf(
        root_path / "quads_f1_chr1.vcf.gz",
        textwrap.dedent("""
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=1>
##contig=<ID=2>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 prb1 mom2 dad2 prb2
1      4   .  T   G   .    .      .    GT     0/1  0/0  0/1  0/1  0/0  0/1
1      8   .  T   G   .    .      .    GT     0/0  0/1  0/1  0/0  0/1  0/1
"""))
    return VcfLoader(
        two_families_ped,
        [str(vcf_path)],
        genome=genome,
    )


@pytest.mark.parametrize(
    "region,count", [
        (Region("1", 4, 4), 1),
        (Region("1", 8, 8), 1),
    ],
)
def test_summary_variants_sharing(
    two_families_vcf: VcfLoader,
    region: Region,
    count: int,
) -> None:
    two_families_vcf.reset_regions([region])
    full_variants = list(two_families_vcf.full_variants_iterator())
    assert len(full_variants) == count
    sv, fvs = full_variants[0]

    for fv in fvs:
        assert id(sv) == id(fv.summary_variant)


@pytest.mark.parametrize(
    "region,count", [
        (Region("1", 4, 4), 1),
        (Region("1", 8, 8), 1),
    ],
)
def test_summary_alleles_sharing(
    two_families_vcf: VcfLoader,
    region: Region,
    count: int,
) -> None:
    two_families_vcf.reset_regions([region])
    full_variants = list(two_families_vcf.full_variants_iterator())
    assert len(full_variants) == count
    sv, fvs = full_variants[0]

    for fv in fvs:
        assert id(sv) == id(fv.summary_variant)
        for sa, fa in zip(sv.alleles, fv.family_alleles, strict=True):
            assert id(sa) == id(fa.summary_allele)
