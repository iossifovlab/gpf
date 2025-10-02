# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import textwrap

import numpy as np
import pytest
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.testing import (
    build_filesystem_test_resource,
    setup_directories,
    setup_genome,
    setup_pedigree,
    setup_vcf,
)
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.utils.regions import Region
from dae.variants.attributes import GeneticModel
from dae.variants_loaders.raw.loader import VariantsGenotypesLoader
from dae.variants_loaders.vcf.loader import VcfLoader


@pytest.fixture(scope="module")
def genome(tmp_path_factory: pytest.TempPathFactory) -> ReferenceGenome:
    root_path = tmp_path_factory.mktemp("genome")
    setup_genome(
        root_path / "chr.fa",
        f"""
        >1
        {25 * "ACGT"}
        >2
        {25 * "ACGT"}
        >X
        {25 * "ACGT"}
        >Y
        {25 * "ACGT"}
        """,
    )

    setup_directories(root_path, {
        GR_CONF_FILE_NAME: """
            type: genome
            filename: chr.fa
            PARS:
                X:
                    - "X:50-60"
                    - "X:90-100"
                Y:
                    - "Y:50-60"
                    - "Y:90-100"
        """,
    })
    res = build_filesystem_test_resource(root_path)
    return build_reference_genome_from_resource(res)


@pytest.fixture(scope="module")
def quads_f1_ped(tmp_path_factory: pytest.TempPathFactory) -> FamiliesData:
    root_path = tmp_path_factory.mktemp("quads_f1_ped")
    ped_path = setup_pedigree(
        root_path / "quads_f1.ped",
        textwrap.dedent("""
        familyId personId dadId momId sex status role
        f1       mom1     0     0     2   1      mom
        f1       dad1     0     0     1   1      dad
        f1       prb1     dad1  mom1  1   2      prb
        f1       sib1     dad1  mom1  2   2      sib
        """))

    return FamiliesLoader(ped_path).load()


@pytest.fixture(scope="module")
def quads_f1(
    tmp_path_factory: pytest.TempPathFactory,
    quads_f1_ped: FamiliesData,
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
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 prb1 sib1
1      4   .  T   G   .    .      .    GT     0/1  0/0  0/1  0/0
2      4   .  T   G   .    .      .    GT     0/0  0/1  0/1  0/0
2      8   .  T   G   .    .      .    GT     0/0  0/1  0/0  0/1
X      4   .  T   G   .    .      .    GT     0/1  0    1    0/0
X      8   .  T   G   .    .      .    GT     0/0  0/1  0/1  0/0
X      52  .  T   G   .    .      .    GT     0/0  0/1  0/1  0/0
X      64  .  T   G   .    .      .    GT     0/0  0    1    0/0
X      92  .  T   G   .    .      .    GT     0/0  0/1  0/0  0/1
"""))
    return VcfLoader(
        quads_f1_ped,
        [str(vcf_path)],
        genome=genome,
    )


@pytest.mark.parametrize(
    "region,count,expected",
    [
        (Region("1", 4, 4), 1, [[True, True]]),  # duploid
        (Region("2", 4, 4), 1, [[True, True]]),  # duploid
        (Region("2", 8, 8), 1, [[True, True]]),  # duploid
        (Region("X", 4, 4), 1, [[False, False]]),
        (Region("X", 52, 52), 1, [[True, True]]),  # psuedo autosomal
        (Region("X", 64, 64), 1, [[False, False]]),
        (Region("X", 92, 92), 1, [[True, True]]),  # psuedo autosomal
    ],
)
def test_get_diploid_males(
    quads_f1: VcfLoader,
    region: Region,
    count: int,
    expected: list[bool],
) -> None:

    quads_f1.reset_regions([region])
    result = []
    for _sv, fvs in quads_f1.full_variants_iterator():
        result.extend(fvs)
    assert len(result) == count
    assert [
        VariantsGenotypesLoader._get_diploid_males(fv)
        for fv in result
    ] == expected


@pytest.mark.parametrize(
    "region,count,expected",
    [
        (Region("1", 4, 4), 1, GeneticModel.autosomal),  # duploid
        (Region("2", 4, 4), 1, GeneticModel.autosomal),  # duploid
        (Region("2", 8, 8), 1, GeneticModel.autosomal),  # duploid
        (Region("X", 4, 4), 1, GeneticModel.X),
        (Region("X", 8, 8), 1, GeneticModel.X_broken),
        (Region("X", 52, 52), 1, GeneticModel.pseudo_autosomal),
        (Region("X", 64, 64), 1, GeneticModel.X),
        (Region("X", 92, 92), 1, GeneticModel.pseudo_autosomal),
    ],
)
def test_vcf_loader_genetic_model(
    quads_f1: VcfLoader,
    region: Region,
    count: int,
    expected: GeneticModel,
) -> None:
    quads_f1.reset_regions([region])
    result = []
    for _sv, fvs in quads_f1.full_variants_iterator():
        result.extend(fvs)
    assert len(result) == count
    fv = result[0]
    assert fv._genetic_model is not None
    for fa in fv.alleles:
        assert fa._genetic_model is not None

    assert fv.genetic_model == expected
    for fa in fv.alleles:
        assert fa._genetic_model == expected


@pytest.mark.parametrize(
    "region,count,expected",
    [
        (Region("1", 4, 4), 1, np.array([[1, 2, 1, 2], [1, 0, 1, 0]])),
        (Region("2", 4, 4), 1, np.array([[2, 1, 1, 2], [0, 1, 1, 0]])),
        (Region("2", 8, 8), 1, np.array([[2, 1, 2, 1], [0, 1, 0, 1]])),
        (Region("X", 4, 4), 1, np.array([[1, 1, 0, 2], [1, 0, 1, 0]])),
        (Region("X", 52, 52), 1, np.array([[2, 1, 1, 2], [0, 1, 1, 0]])),
        (Region("X", 64, 64), 1, np.array([[2, 1, 0, 2], [0, 0, 1, 0]])),
        (Region("X", 92, 92), 1, np.array([[2, 1, 2, 1], [0, 1, 0, 1]])),
    ],
)
def test_vcf_loader_best_state(
    quads_f1: VcfLoader,
    region: Region,
    count: int,
    expected: np.ndarray,
) -> None:

    result = []
    quads_f1.reset_regions([region])
    for _sv, fvs in quads_f1.full_variants_iterator():
        result.extend(fvs)
    assert len(result) == count
    fv = result[0]
    assert fv._best_state is not None
    for fa in fv.alleles:
        assert fa._best_state is not None

    assert np.array_equal(fv.best_state, expected)
    for fa in fv.alleles:
        assert np.array_equal(fa.best_state, expected)
