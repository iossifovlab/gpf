# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
from typing import cast

import numpy as np
import pandas as pd
import pytest
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.testing import setup_denovo, setup_pedigree
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.testing.alla_import import alla_gpf
from dae.utils.variant_utils import GenotypeType, mat2str
from dae.variants.attributes import Inheritance
from dae.variants.family_variant import FamilyAllele, FamilyVariant
from dae.variants_loaders.dae.loader import DenovoLoader


@pytest.fixture
def expected_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "chrom": ["1", "2", "2", "3"],
            "position": [1, 1, 5, 1],
            "reference": ["A", "A", "A", "A"],
            "alternative": ["T", "T", "T", "T"],
            "family_id": ["f1", "f1", "f2", "f3"],
            "genotype": [None, None, None, None],
            "best_state": [
                np.array([[2, 2, 1, 2], [0, 0, 1, 0]]),
                np.array([[2, 2, 1, 2], [0, 0, 1, 0]]),
                np.array([[2, 2, 1], [0, 0, 1]]),
                np.array([[1], [1]]),
            ],
        },
    )


def compare_variant_dfs(
        res_df: pd.DataFrame, expected_df: pd.DataFrame) -> bool:
    equal = True

    # The genotype and best_state columns must be
    # compared separately since they contain numpy arrays

    for col in ("genotype", "best_state"):
        res_genotype = res_df.loc[:, col]
        expected_genotype = expected_df.loc[:, col]
        del res_df[col]
        del expected_df[col]

        assert len(res_genotype) == len(expected_genotype)

        equal = equal and len(res_genotype) == len(expected_genotype)
        # pylint: disable=consider-using-enumerate
        for i in range(len(res_genotype)):
            assert np.array_equal(res_genotype[i], expected_genotype[i]), (
                expected_df.loc[i, :],
                res_df.loc[i, :],
            )

            equal = equal and np.array_equal(
                res_genotype[i], expected_genotype[i],
            )
    print(res_df)
    print(expected_df)
    assert res_df.equals(expected_df)

    return equal and res_df.equals(expected_df)


def test_produce_genotype(
    denovo_families: FamiliesData,
    acgt_genome_19: ReferenceGenome,
) -> None:
    expected_output = np.array([[0, 0, 0, 0], [0, 0, 1, 1]])
    output = DenovoLoader.produce_genotype(
        "1", 1, acgt_genome_19,
        denovo_families["f1"], ["p1", "s1"],
    )
    assert np.array_equal(output, expected_output)
    assert output.dtype == GenotypeType


def test_produce_genotype_no_people_with_variants(
    denovo_families: FamiliesData,
    acgt_genome_19: ReferenceGenome,
) -> None:
    expected_output = np.array([[0, 0, 0, 0], [0, 0, 0, 0]])
    output = DenovoLoader.produce_genotype(
        "1", 1, acgt_genome_19,
        denovo_families["f1"], [],
    )
    assert np.array_equal(output, expected_output)
    assert output.dtype == GenotypeType


def test_families_instance_type_assertion(
    denovo_default_style: pathlib.Path,
    denovo_families: FamiliesData,
    acgt_genome_19: ReferenceGenome,
) -> None:
    error_message = "families must be an instance of FamiliesData!"
    loader = DenovoLoader(
        denovo_families, str(denovo_default_style),
        genome=acgt_genome_19)
    with pytest.raises(AssertionError) as excinfo:
        loader.flexible_denovo_load(
            None,  # type: ignore
            None,  # type: ignore
            denovo_location="foo",
            denovo_variant="bar",
            denovo_person_id="baz",
            families="bla",  # type: ignore
        )
    assert str(excinfo.value) == error_message


def test_read_variants_dae_style(
    denovo_dae_style: pathlib.Path,
    denovo_families: FamiliesData,
    acgt_genome_19: ReferenceGenome,
    expected_df: pd.DataFrame,
) -> None:
    loader = DenovoLoader(
        denovo_families, str(denovo_dae_style),
        genome=acgt_genome_19,
        params={
            "denovo_location": "location",
            "denovo_variant": "variant",
            "denovo_family_id": "familyId",
            "denovo_best_state": "bestState",
        })
    res_df = loader.flexible_denovo_load(
        str(denovo_dae_style),
        acgt_genome_19,
        families=denovo_families,
        denovo_location="location",
        denovo_variant="variant",
        denovo_family_id="familyId",
        denovo_best_state="bestState",
    )

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_a_la_vcf_style(
    denovo_vcf_style: pathlib.Path,
    denovo_families: FamiliesData,
    acgt_genome_19: ReferenceGenome,
    expected_df: pd.DataFrame,
) -> None:
    loader = DenovoLoader(
        denovo_families, str(denovo_vcf_style),
        acgt_genome_19,
        params={
            "denovo_chrom": "chrom",
            "denovo_pos": "pos",
            "denovo_ref": "ref",
            "denovo_alt": "alt",
            "denovo_family_id": "familyId",
            "denovo_best_state": "bestState",
        })
    res_df = loader.flexible_denovo_load(
        str(denovo_vcf_style),
        acgt_genome_19,
        families=denovo_families,
        denovo_chrom="chrom",
        denovo_pos="pos",
        denovo_ref="ref",
        denovo_alt="alt",
        denovo_family_id="familyId",
        denovo_best_state="bestState",
    )

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_mixed_a(
    tmp_path: pathlib.Path,
    denovo_families: FamiliesData,
    acgt_genome_19: ReferenceGenome,
    expected_df: pd.DataFrame,
) -> None:
    filename = setup_denovo(tmp_path / "mixed_style_A.tsv", textwrap.dedent("""
familyId location ref  alt  bestState
f1       1:1      A    T    2||2||1||2/0||0||1||0
f1       2:1      A    T    2||2||1||2/0||0||1||0
f2       2:5      A    T    2||2||1/0||0||1
f3       3:1      A    T    1/1
"""))

    loader = DenovoLoader(
        denovo_families, str(filename), acgt_genome_19,
        params={
            "denovo_location": "location",
            "denovo_ref": "ref",
            "denovo_alt": "alt",
            "denovo_family_id": "familyId",
            "denovo_best_state": "bestState",
        })
    res_df = loader.flexible_denovo_load(
        str(filename),
        acgt_genome_19,
        families=denovo_families,
        denovo_location="location",
        denovo_ref="ref",
        denovo_alt="alt",
        denovo_family_id="familyId",
        denovo_best_state="bestState",
    )

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_mixed_b(
    tmp_path: pathlib.Path,
    denovo_families: FamiliesData,
    acgt_genome_19: ReferenceGenome,
    expected_df: pd.DataFrame,
) -> None:
    filename = setup_denovo(tmp_path / "mixed_style_A.tsv", textwrap.dedent("""
familyId chrom pos variant     bestState
f1       1     1   sub(A->T)   2||2||1||2/0||0||1||0
f1       2     1   sub(A->T)   2||2||1||2/0||0||1||0
f2       2     5   sub(A->T)   2||2||1/0||0||1
f3       3     1   sub(A->T)   1/1
"""))

    loader = DenovoLoader(
        denovo_families,
        str(filename),
        acgt_genome_19,
        params={
            "denovo_chrom": "chrom",
            "denovo_pos": "pos",
            "denovo_variant": "variant",
            "denovo_family_id": "familyId",
            "denovo_best_state": "bestState",
        })
    res_df = loader.flexible_denovo_load(
        str(filename),
        acgt_genome_19,
        families=denovo_families,
        denovo_chrom="chrom",
        denovo_pos="pos",
        denovo_variant="variant",
        denovo_family_id="familyId",
        denovo_best_state="bestState",
    )

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_person_ids_multiline(
    tmp_path: pathlib.Path,
    denovo_families: FamiliesData,
    acgt_genome_19: ReferenceGenome,
) -> None:
    filename = setup_denovo(tmp_path / "multi_person.tsv", textwrap.dedent("""
personId chrom pos  ref alt familyId
p1       1     1    A   T   f1
s1       1     1    A   T   f1
"""))
    loader = DenovoLoader(
        denovo_families, str(filename),
        acgt_genome_19,
        params={
            "denovo_chrom": "chrom",
            "denovo_pos": "pos",
            "denovo_ref": "ref",
            "denovo_alt": "alt",
            "denovo_person_id": "personId",
            "denovo_family_id": "familyId",
        })
    res_df = loader.flexible_denovo_load(
        str(filename),
        acgt_genome_19,
        families=denovo_families,
        denovo_chrom="chrom",
        denovo_pos="pos",
        denovo_ref="ref",
        denovo_alt="alt",
        denovo_person_id="personId",
        denovo_family_id="familyId",
    )

    assert len(res_df) == 1

    expected_df = pd.DataFrame(
        {
            "chrom": ["1"],
            "position": [1],
            "reference": ["A"],
            "alternative": ["T"],
            "family_id": ["f1"],
            "genotype": [
                np.array([[0, 0, 0, 0], [0, 0, 1, 1]]),
            ],
            "best_state": [None],
        },
    )

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_person_ids_list(
    tmp_path: pathlib.Path,
    denovo_families: FamiliesData,
    acgt_genome_19: ReferenceGenome,
) -> None:
    filename = setup_denovo(tmp_path / "multi_person.tsv", textwrap.dedent("""
personId chrom pos  ref alt
p1,s1    1     1    A   T
"""))
    loader = DenovoLoader(
        denovo_families, str(filename),
        acgt_genome_19,
        params={
            "denovo_chrom": "chrom",
            "denovo_pos": "pos",
            "denovo_ref": "ref",
            "denovo_alt": "alt",
            "denovo_person_id": "personId",
        })
    res_df = loader.flexible_denovo_load(
        str(filename),
        acgt_genome_19,
        families=denovo_families,
        denovo_chrom="chrom",
        denovo_pos="pos",
        denovo_ref="ref",
        denovo_alt="alt",
        denovo_person_id="personId",
    )

    assert len(res_df) == 1

    expected_df = pd.DataFrame(
        {
            "chrom": ["1"],
            "position": [1],
            "reference": ["A"],
            "alternative": ["T"],
            "family_id": ["f1"],
            "genotype": [
                np.array([[0, 0, 0, 0], [0, 0, 1, 1]]),
            ],
            "best_state": [None],
        },
    )

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_different_separator(
    tmp_path: pathlib.Path,
    denovo_families: FamiliesData,
    acgt_genome_19: ReferenceGenome,
    expected_df: pd.DataFrame,
) -> None:
    filename = setup_denovo(tmp_path / "separator.tsv", textwrap.dedent("""
familyId$chrom$pos$ref$alt$bestState
f1$1$1$A$T$2||2||1||2/0||0||1||0
f1$2$1$A$T$2||2||1||2/0||0||1||0
f2$2$5$A$T$2||2||1/0||0||1
f3$3$1$A$T$1/1
"""))

    loader = DenovoLoader(
        denovo_families, str(filename), acgt_genome_19,
        params={
            "denovo_sep": "$",
            "denovo_chrom": "chrom",
            "denovo_pos": "pos",
            "denovo_ref": "ref",
            "denovo_alt": "alt",
            "denovo_family_id": "familyId",
            "denovo_best_state": "bestState",
        })
    res_df = loader.flexible_denovo_load(
        str(filename),
        acgt_genome_19,
        families=denovo_families,
        denovo_sep="$",
        denovo_chrom="chrom",
        denovo_pos="pos",
        denovo_ref="ref",
        denovo_alt="alt",
        denovo_family_id="familyId",
        denovo_best_state="bestState",
    )

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_with_genotype(
    tmp_path: pathlib.Path,
    denovo_families: FamiliesData,
    acgt_genome_19: ReferenceGenome,
) -> None:
    filename = setup_denovo(tmp_path / "separator.tsv", textwrap.dedent("""
familyId chrom pos  ref alt genotype
f1       1     1    A   T   0/0,0/0,0/1,0/0
f1       2     1    A   T   0/0,0/0,0/1,0/0
f2       2     5    A   T   0/0,0/0,0/1
f3       3     1    A   T   0/1
"""))
    loader = DenovoLoader(
        denovo_families, str(filename),
        acgt_genome_19,
        params={
            "denovo_chrom": "chrom",
            "denovo_pos": "pos",
            "denovo_ref": "ref",
            "denovo_alt": "alt",
            "denovo_family_id": "familyId",
            "denovo_genotype": "genotype",
        })
    res_df = loader.flexible_denovo_load(
        str(filename),
        acgt_genome_19,
        families=denovo_families,
        denovo_chrom="chrom",
        denovo_pos="pos",
        denovo_ref="ref",
        denovo_alt="alt",
        denovo_family_id="familyId",
        denovo_genotype="genotype",
    )

    expected_df = pd.DataFrame({
        "chrom": ["1", "2", "2", "3"],
        "position": [1, 1, 5, 1],
        "reference": ["A", "A", "A", "A"],
        "alternative": ["T", "T", "T", "T"],
        "family_id": ["f1", "f1", "f2", "f3"],
        "genotype": [
            np.array([[0, 0, 0, 0], [0, 0, 1, 0]]),
            np.array([[0, 0, 0, 0], [0, 0, 1, 0]]),
            np.array([[0, 0, 0], [0, 0, 1]]),
            np.array([[0], [1]]),
        ],
        "best_state": [
            None, None, None, None,
        ],
    })

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_genome_assertion(
    denovo_default_style: pathlib.Path,
    denovo_families: FamiliesData,
    acgt_genome_19: ReferenceGenome,
) -> None:
    loader = DenovoLoader(
        denovo_families, str(denovo_default_style),
        acgt_genome_19)

    with pytest.raises(AssertionError) as excinfo:
        loader.flexible_denovo_load(
            str(denovo_default_style),
            None,  # type: ignore
            families=denovo_families,
        )

    assert str(excinfo.value) == "You must provide a genome object!"


@pytest.fixture
def families_fixture(tmp_path: pathlib.Path) -> FamiliesData:
    ped_path = setup_pedigree(
        tmp_path / "pedigree.ped",
        textwrap.dedent("""
        familyId personId dadId  momId  sex status role
        f1       f1.dad   0      0      1   1      dad
        f1       f1.mom   0      0      2   1      mom
        f1       f1.s1    f1.dad f1.mom 2   1      sib
        f1       f1.p1    f1.dad f1.mom 1   2      prb
        f1       f1.s2    f1.dad f1.mom 2   2      sib
        f2       f2.mom   0      0      2   1      mom
        f2       f2.dad   0      0      1   1      dad
        f2       f2.p1    f2.dad f2.mom 1   2      prb
        f2       f2.s1    f2.dad f2.mom 2   1      sib
        f3       f3.p1    0      0      1   2      prb
        """),
    )
    return FamiliesLoader(str(ped_path)).load()


@pytest.mark.parametrize("variants,params", [
    (textwrap.dedent("""
        familyId location variant   bestState
        f1       chr1:1   sub(A->G) 2||2||1||2||1/0||0||1||0||1
        f2       chr1:2   sub(A->G) 2||2||2||1/0||0||0||1
        f3       chr1:3   sub(A->G) 1/1
        """), {
        "denovo_location": "location",
        "denovo_variant": "variant",
        "denovo_family_id": "familyId",
        "denovo_best_state": "bestState",
    }),
    (textwrap.dedent("""
        familyId chrom pos ref alt bestState
        f1       chr1  1   A   G   2||2||1||2||1/0||0||1||0||1
        f2       chr1  2   A   G   2||2||2||1/0||0||0||1
        f3       chr1  3   A   G   1/1
        """), {
        "denovo_chrom": "chrom",
        "denovo_pos": "pos",
        "denovo_ref": "ref",
        "denovo_alt": "alt",
        "denovo_family_id": "familyId",
        "denovo_best_state": "bestState",
    }),
    (textwrap.dedent("""
        familyId location variant   bestState
        f1       chr1:1   sub(A->G) 22121/00101
        f2       chr1:2   sub(A->G) 2221/0001
        f3       chr1:3   sub(A->G) 1/1
        """), {
        "denovo_location": "location",
        "denovo_variant": "variant",
        "denovo_family_id": "familyId",
        "denovo_best_state": "bestState",
    }),
    (textwrap.dedent("""
        familyId chrom pos ref alt bestState
        f1       chr1  1   A   G   22121/00101
        f2       chr1  2   A   G   2221/0001
        f3       chr1  3   A   G   1/1
        """), {
        "denovo_chrom": "chrom",
        "denovo_pos": "pos",
        "denovo_ref": "ref",
        "denovo_alt": "alt",
        "denovo_family_id": "familyId",
        "denovo_best_state": "bestState",
    }),
    (textwrap.dedent("""
        familyId chrom pos ref alt personId
        f1       chr1  1   A   G   f1.s1,f1.s2
        f2       chr1  2   A   G   f2.s1
        f3       chr1  3   A   G   f3.p1
        """), {
        "denovo_chrom": "chrom",
        "denovo_pos": "pos",
        "denovo_ref": "ref",
        "denovo_alt": "alt",
        "denovo_family_id": "familyId",
        "denovo_person_id": "personId",
    }),
    (textwrap.dedent("""
        familyId chrom pos ref alt personId
        f1       chr1  1   A   G   f1.s1;f1.s2
        f2       chr1  2   A   G   f2.s1
        f3       chr1  3   A   G   f3.p1
        """), {
        "denovo_chrom": "chrom",
        "denovo_pos": "pos",
        "denovo_ref": "ref",
        "denovo_alt": "alt",
        "denovo_family_id": "familyId",
        "denovo_person_id": "personId",
    }),
])
def test_denovo_loader_new(
    tmp_path: pathlib.Path,
    families_fixture: FamiliesData,
    variants: str, params: dict[str, str],
) -> None:
    gpf = alla_gpf(tmp_path)
    denovo_path = setup_denovo(tmp_path / "variants.tsv", variants)

    variants_loader = DenovoLoader(
        families_fixture, str(denovo_path),
        genome=gpf.reference_genome, params=params,
        sort=False,
    )

    vs = list(variants_loader.full_variants_iterator())
    print(vs)
    assert len(vs) == 3

    def falt_allele(index: int) -> FamilyAllele:
        return cast(FamilyAllele, vs[index][1][0].alt_alleles[0])

    fa = falt_allele(0)
    assert fa.inheritance_in_members == [
        Inheritance.unknown,
        Inheritance.unknown,
        Inheritance.denovo,
        Inheritance.missing,
        Inheritance.denovo,
    ]
    assert mat2str(fa.best_state) == "22121/00101"

    fa = falt_allele(1)
    assert fa.inheritance_in_members == [
        Inheritance.unknown,
        Inheritance.unknown,
        Inheritance.missing,
        Inheritance.denovo,
    ]
    assert mat2str(fa.best_state) == "2221/0001"

    fa = falt_allele(2)
    assert fa.inheritance_in_members == [
        Inheritance.denovo,
    ]
    assert mat2str(fa.best_state) == "1/1"


def test_denovo_loader_avoids_duplicates(
    tmp_path: pathlib.Path,
    denovo_families: FamiliesData,
    acgt_genome_19: ReferenceGenome,
) -> None:
    filename = setup_denovo(
        tmp_path / "in.tsv", textwrap.dedent("""
familyId chrom pos  ref alt bestState
f1       1     1    A   T   2||2||1||2/0||0||1||0
f1       2     1    A   T   2||2||1||2/0||0||1||0
f2       2     1    A   T   2||2||1/0||0||1
f3       3     1    A   T   1/1
"""))

    params = {
        "denovo_chrom": "chrom",
        "denovo_pos": "pos",
        "denovo_ref": "ref",
        "denovo_alt": "alt",
        "denovo_family_id": "familyId",
        "denovo_best_state": "bestState",
    }
    variants_loader = DenovoLoader(
        denovo_families, str(filename),
        genome=acgt_genome_19,
        params=params,
    )

    variants_iter = variants_loader.full_variants_iterator()

    svs = []
    fvs: list[FamilyVariant] = []
    for sv, fvs_ in variants_iter:
        print(sv, fvs)
        svs.append(sv)
        fvs.extend(fvs_)

    assert len(svs) == 3
    assert len(fvs) == 4


def test_denovo_loader(
    denovo_dae_style: pathlib.Path,
    denovo_families: FamiliesData,
    acgt_genome_19: ReferenceGenome,
) -> None:
    params = {
        "denovo_location": "location",
        "denovo_variant": "variant",
        "denovo_family_id": "familyId",
        "denovo_best_state": "bestState",
    }

    variants_loader = DenovoLoader(
        denovo_families, str(denovo_dae_style),
        genome=acgt_genome_19,
        params=params,
        sort=False,
    )

    variants = list(variants_loader.full_variants_iterator())
    print(variants)

    def falt_allele(index: int) -> FamilyAllele:
        return cast(FamilyAllele, variants[index][1][0].alt_alleles[0])

    fa = falt_allele(0)
    print(fa, fa.variant_in_members, fa.inheritance_in_members)
    assert fa.inheritance_in_members[2] == Inheritance.denovo
    assert fa.inheritance_in_members == [
        Inheritance.unknown,
        Inheritance.unknown,
        Inheritance.denovo,
        Inheritance.missing,
    ]

    fa = falt_allele(1)
    print(fa, fa.variant_in_members, fa.inheritance_in_members)
    assert fa.inheritance_in_members[2] == Inheritance.denovo
    assert fa.inheritance_in_members == [
        Inheritance.unknown,
        Inheritance.unknown,
        Inheritance.denovo,
        Inheritance.missing,
    ]

    fa = falt_allele(2)
    print(fa, fa.variant_in_members, fa.inheritance_in_members)
    assert fa.inheritance_in_members[2] == Inheritance.denovo
    assert fa.inheritance_in_members == [
        Inheritance.unknown,
        Inheritance.unknown,
        Inheritance.denovo,
    ]

    fa = falt_allele(3)
    print(fa, fa.variant_in_members, fa.inheritance_in_members)

    assert fa.inheritance_in_members[0] == Inheritance.denovo
    assert fa.inheritance_in_members == [Inheritance.denovo]
