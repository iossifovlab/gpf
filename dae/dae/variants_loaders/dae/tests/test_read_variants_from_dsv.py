# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
from typing import Callable, cast

import pytest
import pandas as pd
import numpy as np

from dae.pedigrees.family import FamiliesData
from dae.pedigrees.loader import FamiliesLoader

from dae.variants.attributes import Inheritance
from dae.variants.family_variant import FamilyVariant, FamilyAllele
from dae.variants_loaders.dae.loader import DenovoLoader
from dae.utils.variant_utils import GenotypeType, mat2str
from dae.gpf_instance import GPFInstance
from dae.testing import setup_denovo, setup_pedigree, alla_gpf


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
        for i in range(0, len(res_genotype)):
            assert np.array_equal(res_genotype[i], expected_genotype[i]), (
                expected_df.loc[i, :],
                res_df.loc[i, :],
            )

            equal = equal and np.array_equal(
                res_genotype[i], expected_genotype[i]
            )
    print(res_df)
    print(expected_df)
    assert res_df.equals(expected_df)

    return equal and res_df.equals(expected_df)


def test_produce_genotype(
        fake_families: FamiliesData,
        gpf_instance_2013: GPFInstance) -> None:
    expected_output = np.array([[0, 0, 0, 0, 0], [0, 0, 0, 1, 1]])
    output = DenovoLoader.produce_genotype(
        "1", 123123, gpf_instance_2013.reference_genome,
        fake_families["f1"], ["f1.p1", "f1.s2"]
    )
    assert np.array_equal(output, expected_output)
    assert output.dtype == GenotypeType


def test_produce_genotype_no_people_with_variants(
        fake_families: FamiliesData,
        gpf_instance_2013: GPFInstance) -> None:
    expected_output = np.array([[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]])
    output = DenovoLoader.produce_genotype(
        "1", 123123, gpf_instance_2013.reference_genome,
        fake_families["f1"], []
    )
    assert np.array_equal(output, expected_output)
    assert output.dtype == GenotypeType


def test_families_instance_type_assertion(
        fixture_dirname: Callable[[str], str],
        fake_families: FamiliesData,
        gpf_instance_2013: GPFInstance) -> None:
    error_message = "families must be an instance of FamiliesData!"
    filename = fixture_dirname("denovo_import/variants_DAE_style.tsv")
    loader = DenovoLoader(
        fake_families, filename, gpf_instance_2013.reference_genome)
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
        fixture_dirname: Callable[[str], str],
        fake_families: FamiliesData,
        gpf_instance_2013: GPFInstance) -> None:
    filename = fixture_dirname("denovo_import/variants_DAE_style.tsv")
    loader = DenovoLoader(
        fake_families, filename, gpf_instance_2013.reference_genome)
    res_df = loader.flexible_denovo_load(
        filename,
        gpf_instance_2013.reference_genome,
        families=fake_families,
        denovo_location="location",
        denovo_variant="variant",
        denovo_family_id="familyId",
        denovo_best_state="bestState",
    )

    expected_df = pd.DataFrame(
        {
            "chrom": ["1", "2", "2", "3", "4"],
            "position": [123, 234, 234, 345, 456],
            "reference": ["A", "T", "G", "G", "G"],
            "alternative": ["G", "A", "A", "A", "A"],
            "family_id": ["f1", "f1", "f2", "f3", "f4"],
            "genotype": [None, None, None, None, None],
            "best_state": [
                np.array([[2, 2, 1, 2, 1], [0, 0, 1, 0, 1]]),
                np.array([[2, 2, 1, 2, 2], [0, 0, 1, 0, 0]]),
                np.array([[2, 2, 2, 1], [0, 0, 0, 1]]),
                np.array([[1], [1]]),
                np.array([[1, 1], [1, 1]]),
            ],
        }
    )

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_a_la_vcf_style(
        fixture_dirname: Callable[[str], str],
        fake_families: FamiliesData,
        gpf_instance_2013: GPFInstance) -> None:
    filename = fixture_dirname("denovo_import/variants_VCF_style.tsv")
    loader = DenovoLoader(
        fake_families, filename, gpf_instance_2013.reference_genome,
        params={
            "denovo_chrom": "chrom",
            "denovo_pos": "pos",
            "denovo_ref": "ref",
            "denovo_alt": "alt",
            "denovo_family_id": "familyId",
            "denovo_best_state": "bestState",
        })
    res_df = loader.flexible_denovo_load(
        filename,
        gpf_instance_2013.reference_genome,
        families=fake_families,
        denovo_chrom="chrom",
        denovo_pos="pos",
        denovo_ref="ref",
        denovo_alt="alt",
        denovo_family_id="familyId",
        denovo_best_state="bestState",
    )

    expected_df = pd.DataFrame(
        {
            "chrom": ["1", "2", "2", "3", "4"],
            "position": [123, 234, 234, 345, 456],
            "reference": ["A", "T", "G", "G", "G"],
            "alternative": ["G", "A", "A", "A", "A"],
            "family_id": ["f1", "f1", "f2", "f3", "f4"],
            "genotype": [None, None, None, None, None],
            "best_state": [
                np.array([[2, 2, 1, 2, 1], [0, 0, 1, 0, 1]]),
                np.array([[2, 2, 1, 2, 2], [0, 0, 1, 0, 0]]),
                np.array([[2, 2, 2, 1], [0, 0, 0, 1]]),
                np.array([[1], [1]]),
                np.array([[1, 1], [1, 1]]),
            ],
        }
    )

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_mixed_a(
        fixture_dirname: Callable[[str], str],
        fake_families: FamiliesData,
        gpf_instance_2013: GPFInstance) -> None:
    filename = fixture_dirname("denovo_import/variants_mixed_style_A.tsv")
    loader = DenovoLoader(
        fake_families, filename, gpf_instance_2013.reference_genome,
        params={
            "denovo_location": "location",
            "denovo_ref": "ref",
            "denovo_alt": "alt",
            "denovo_family_id": "familyId",
            "denovo_best_state": "bestState",
        })
    res_df = loader.flexible_denovo_load(
        filename,
        gpf_instance_2013.reference_genome,
        families=fake_families,
        denovo_location="location",
        denovo_ref="ref",
        denovo_alt="alt",
        denovo_family_id="familyId",
        denovo_best_state="bestState",
    )

    expected_df = pd.DataFrame(
        {
            "chrom": ["1", "2", "2", "3", "4"],
            "position": [123, 234, 234, 345, 456],
            "reference": ["A", "T", "G", "G", "G"],
            "alternative": ["G", "A", "A", "A", "A"],
            "family_id": ["f1", "f1", "f2", "f3", "f4"],
            "genotype": [None, None, None, None, None],
            "best_state": [
                np.array([[2, 2, 1, 2, 1], [0, 0, 1, 0, 1]]),
                np.array([[2, 2, 1, 2, 2], [0, 0, 1, 0, 0]]),
                np.array([[2, 2, 2, 1], [0, 0, 0, 1]]),
                np.array([[1], [1]]),
                np.array([[1, 1], [1, 1]]),
            ],
        }
    )

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_mixed_b(
        fixture_dirname: Callable[[str], str],
        fake_families: FamiliesData,
        gpf_instance_2013: GPFInstance) -> None:
    filename = fixture_dirname("denovo_import/variants_mixed_style_B.tsv")
    loader = DenovoLoader(
        fake_families, filename, gpf_instance_2013.reference_genome,
        params={
            "denovo_chrom": "chrom",
            "denovo_pos": "pos",
            "denovo_variant": "variant",
            "denovo_family_id": "familyId",
            "denovo_best_state": "bestState",
        })
    res_df = loader.flexible_denovo_load(
        filename,
        gpf_instance_2013.reference_genome,
        families=fake_families,
        denovo_chrom="chrom",
        denovo_pos="pos",
        denovo_variant="variant",
        denovo_family_id="familyId",
        denovo_best_state="bestState",
    )

    expected_df = pd.DataFrame(
        {
            "chrom": ["1", "2", "2", "3", "4"],
            "position": [123, 234, 234, 345, 456],
            "reference": ["A", "T", "G", "G", "G"],
            "alternative": ["G", "A", "A", "A", "A"],
            "family_id": ["f1", "f1", "f2", "f3", "f4"],
            "genotype": [None, None, None, None, None],
            "best_state": [
                np.array([[2, 2, 1, 2, 1], [0, 0, 1, 0, 1]]),
                np.array([[2, 2, 1, 2, 2], [0, 0, 1, 0, 0]]),
                np.array([[2, 2, 2, 1], [0, 0, 0, 1]]),
                np.array([[1], [1]]),
                np.array([[1, 1], [1, 1]]),
            ],
        }
    )

    assert compare_variant_dfs(res_df, expected_df)


@pytest.mark.parametrize(
    "filename",
    [
        ("denovo_import/variants_personId_single.tsv"),
        ("denovo_import/variants_personId_list.tsv"),
    ],
)
def test_read_variants_person_ids(
        filename: str,
        fixture_dirname: Callable[[str], str],
        fake_families: FamiliesData,
        gpf_instance_2013: GPFInstance) -> None:
    filename = fixture_dirname(filename)
    loader = DenovoLoader(
        fake_families, filename, gpf_instance_2013.reference_genome,
        params={
            "denovo_chrom": "chrom",
            "denovo_pos": "pos",
            "denovo_ref": "ref",
            "denovo_alt": "alt",
            "denovo_person_id": "personId",
        })
    res_df = loader.flexible_denovo_load(
        filename,
        gpf_instance_2013.reference_genome,
        families=fake_families,
        denovo_chrom="chrom",
        denovo_pos="pos",
        denovo_ref="ref",
        denovo_alt="alt",
        denovo_person_id="personId",
    )

    expected_df = pd.DataFrame(
        {
            "chrom": ["1", "2", "2", "3", "4"],
            "position": [123, 234, 235, 345, 456],
            "reference": ["A", "T", "G", "G", "G"],
            "alternative": ["G", "A", "A", "A", "A"],
            "family_id": ["f1", "f1", "f2", "f3", "f4"],
            "genotype": [
                np.array([[0, 0, 0, 0, 0], [0, 0, 1, 0, 1]]),
                np.array([[0, 0, 0, 0, 0], [0, 0, 1, 0, 0]]),
                np.array([[0, 0, 0, 0], [0, 0, 0, 1]]),
                np.array([[0], [1]]),
                np.array([[0, 0], [1, 1]]),
            ],
            "best_state": [None, None, None, None, None],
        }
    )

    print(res_df)
    print(expected_df)

    res_df = res_df.sort_values(["chrom", "position", "reference"])
    res_df = res_df.reset_index(drop=True)
    expected_df = expected_df.sort_values(["chrom", "position", "reference"])
    expected_df = expected_df.reset_index(drop=True)

    print(res_df)
    print(expected_df)

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_different_separator(
        fixture_dirname: Callable[[str], str],
        fake_families: FamiliesData,
        gpf_instance_2013: GPFInstance) -> None:
    filename = fixture_dirname(
        "denovo_import/variants_different_separator.dsv"
    )
    loader = DenovoLoader(
        fake_families, filename, gpf_instance_2013.reference_genome,
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
        filename,
        gpf_instance_2013.reference_genome,
        families=fake_families,
        denovo_sep="$",
        denovo_chrom="chrom",
        denovo_pos="pos",
        denovo_ref="ref",
        denovo_alt="alt",
        denovo_family_id="familyId",
        denovo_best_state="bestState",
    )

    expected_df = pd.DataFrame(
        {
            "chrom": ["1", "2", "2", "3", "4"],
            "position": [123, 234, 234, 345, 456],
            "reference": ["A", "T", "G", "G", "G"],
            "alternative": ["G", "A", "A", "A", "A"],
            "family_id": ["f1", "f1", "f2", "f3", "f4"],
            "genotype": [None, None, None, None, None],
            "best_state": [
                np.array([[2, 2, 1, 2, 1], [0, 0, 1, 0, 1]]),
                np.array([[2, 2, 1, 2, 2], [0, 0, 1, 0, 0]]),
                np.array([[2, 2, 2, 1], [0, 0, 0, 1]]),
                np.array([[1], [1]]),
                np.array([[1, 1], [1, 1]]),
            ],
        }
    )

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_with_genotype(
        fixture_dirname: Callable[[str], str],
        fake_families: FamiliesData,
        gpf_instance_2013: GPFInstance) -> None:
    filename = fixture_dirname(
        "denovo_import/variants_VCF_genotype.tsv"
    )
    loader = DenovoLoader(
        fake_families, filename, gpf_instance_2013.reference_genome,
        params={
            "denovo_chrom": "chrom",
            "denovo_pos": "pos",
            "denovo_ref": "ref",
            "denovo_alt": "alt",
            "denovo_family_id": "familyId",
            "denovo_genotype": "genotype",
        })
    res_df = loader.flexible_denovo_load(
        filename,
        gpf_instance_2013.reference_genome,
        families=fake_families,
        denovo_chrom="chrom",
        denovo_pos="pos",
        denovo_ref="ref",
        denovo_alt="alt",
        denovo_family_id="familyId",
        denovo_genotype="genotype",
    )

    expected_df = pd.DataFrame(
        {
            "chrom": ["1", "2", "2", "3", "4"],
            "position": [123, 234, 234, 345, 456],
            "reference": ["A", "T", "G", "G", "G"],
            "alternative": ["G", "A", "A", "A", "A"],
            "family_id": ["f1", "f1", "f2", "f3", "f4"],
            "genotype": [
                np.array([[0, 0, 0, 0, 0], [0, 0, 1, 0, 1]]),
                np.array([[0, 0, 0, 0, 0], [0, 0, 1, 0, 0]]),
                np.array([[0, 0, 0, 0], [0, 0, 0, 1]]),
                np.array([[0], [1]]),
                np.array([[0, 0], [1, 1]]),
            ],
            "best_state": [
                None,
                None,
                None,
                None,
                None,
            ],
        }
    )

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_genome_assertion(
        fixture_dirname: Callable[[str], str],
        fake_families: FamiliesData,
        gpf_instance_2013: GPFInstance) -> None:
    filename = fixture_dirname("denovo_import/variants_DAE_style.tsv")

    with pytest.raises(AssertionError) as excinfo:
        loader = DenovoLoader(
            fake_families, filename, gpf_instance_2013.reference_genome)
        loader.flexible_denovo_load(
            filename,
            None,  # type: ignore
            families=fake_families,
            denovo_location="location",
            denovo_variant="variant",
            denovo_family_id="familyId",
            denovo_best_state="bestState",
        )

    assert str(excinfo.value) == "You must provide a genome object!"


@pytest.mark.parametrize(
    "filename,params",
    [
        (
            "variants_DAE_style.tsv",
            {
                "denovo_location": "location",
                "denovo_variant": "variant",
                "denovo_family_id": "familyId",
                "denovo_best_state": "bestState",
            },
        ),
        (
            "variants_VCF_style.tsv",
            {
                "denovo_chrom": "chrom",
                "denovo_pos": "pos",
                "denovo_ref": "ref",
                "denovo_alt": "alt",
                "denovo_family_id": "familyId",
                "denovo_best_state": "bestState",
            },
        ),
        (
            "variants_mixed_style_A.tsv",
            {
                "denovo_location": "location",
                "denovo_ref": "ref",
                "denovo_alt": "alt",
                "denovo_family_id": "familyId",
                "denovo_best_state": "bestState",
            },
        ),
        (
            "variants_mixed_style_B.tsv",
            {
                "denovo_chrom": "chrom",
                "denovo_pos": "pos",
                "denovo_variant": "variant",
                "denovo_family_id": "familyId",
                "denovo_best_state": "bestState",
            },
        ),
        (
            "variants_personId_single.tsv",
            {
                "denovo_chrom": "chrom",
                "denovo_pos": "pos",
                "denovo_ref": "ref",
                "denovo_alt": "alt",
                "denovo_person_id": "personId",
            },
        ),
        (
            "variants_personId_list.tsv",
            {
                "denovo_chrom": "chrom",
                "denovo_pos": "pos",
                "denovo_ref": "ref",
                "denovo_alt": "alt",
                "denovo_person_id": "personId",
            },
        ),
        (
            "variants_different_separator.dsv",
            {
                "denovo_sep": "$",
                "denovo_chrom": "chrom",
                "denovo_pos": "pos",
                "denovo_ref": "ref",
                "denovo_alt": "alt",
                "denovo_family_id": "familyId",
                "denovo_best_state": "bestState",
            },
        ),
    ],
)
def test_denovo_loader(
        filename: str, params: dict[str, str],
        fixture_dirname: Callable[[str], str],
        fake_families: FamiliesData,
        gpf_instance_2013: GPFInstance) -> None:
    denovo_filename = fixture_dirname(f"denovo_import/{filename}")
    variants_loader = DenovoLoader(
        fake_families, denovo_filename,
        genome=gpf_instance_2013.reference_genome, params=params,
        sort=False
    )

    variants = list(variants_loader.full_variants_iterator())
    print(variants)

    def falt_allele(index: int) -> FamilyAllele:
        return cast(FamilyAllele, variants[index][1][0].alt_alleles[0])

    fa = falt_allele(0)
    print(fa, fa.variant_in_members, fa.inheritance_in_members)
    assert fa.inheritance_in_members[2] == Inheritance.denovo
    assert fa.inheritance_in_members[4] == Inheritance.denovo
    assert fa.inheritance_in_members == [
        Inheritance.unknown,
        Inheritance.unknown,
        Inheritance.denovo,
        Inheritance.missing,
        Inheritance.denovo,
    ]

    fa = falt_allele(1)
    print(fa, fa.variant_in_members, fa.inheritance_in_members)
    assert fa.inheritance_in_members[2] == Inheritance.denovo
    assert fa.inheritance_in_members == [
        Inheritance.unknown,
        Inheritance.unknown,
        Inheritance.denovo,
        Inheritance.missing,
        Inheritance.missing,
    ]

    fa = falt_allele(2)
    print(fa, fa.variant_in_members, fa.inheritance_in_members)
    assert fa.inheritance_in_members[3] == Inheritance.denovo
    assert fa.inheritance_in_members == [
        Inheritance.unknown,
        Inheritance.unknown,
        Inheritance.missing,
        Inheritance.denovo,
    ]

    fa = falt_allele(3)
    print(fa, fa.variant_in_members, fa.inheritance_in_members)

    assert fa.inheritance_in_members[0] == Inheritance.denovo
    assert fa.inheritance_in_members == [Inheritance.denovo]

    fa = falt_allele(4)
    print(fa, fa.variant_in_members, fa.inheritance_in_members)

    assert fa.inheritance_in_members[0] == Inheritance.denovo
    assert fa.inheritance_in_members == [
        Inheritance.denovo,
        Inheritance.denovo,
    ]


def test_denovo_loader_avoids_duplicates(
        fixture_dirname: Callable[[str], str],
        fake_families: FamiliesData,
        gpf_instance_2013: GPFInstance) -> None:
    denovo_filename = fixture_dirname(
        "denovo_import/variants_VCF_style_dup.tsv"
    )
    params = {
        "denovo_chrom": "chrom",
        "denovo_pos": "pos",
        "denovo_ref": "ref",
        "denovo_alt": "alt",
        "denovo_family_id": "familyId",
        "denovo_best_state": "bestState"
    }
    variants_loader = DenovoLoader(
        fake_families, denovo_filename,
        genome=gpf_instance_2013.reference_genome, params=params
    )

    variants_iter = variants_loader.full_variants_iterator()

    svs = []
    fvs: list[FamilyVariant] = []
    for sv, fvs_ in variants_iter:
        print(sv, fvs)
        svs.append(sv)
        for fv in fvs_:
            fvs.append(fv)

    assert len(svs) == 3
    assert len(fvs) == 4


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
        """)
    )
    return FamiliesLoader(str(ped_path)).load()


@pytest.mark.parametrize("variants,params", [
    (textwrap.dedent("""
        familyId location variant   bestState
        f1       chrA:1   sub(A->G) 2||2||1||2||1/0||0||1||0||1
        f2       chrA:2   sub(A->G) 2||2||2||1/0||0||0||1
        f3       chrA:3   sub(A->G) 1/1
        """), {
        "denovo_location": "location",
        "denovo_variant": "variant",
        "denovo_family_id": "familyId",
        "denovo_best_state": "bestState",
    }),
    (textwrap.dedent("""
        familyId chrom pos ref alt bestState
        f1       chrA  1   A   G   2||2||1||2||1/0||0||1||0||1
        f2       chrA  2   A   G   2||2||2||1/0||0||0||1
        f3       chrA  3   A   G   1/1
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
        f1       chrA:1   sub(A->G) 22121/00101
        f2       chrA:2   sub(A->G) 2221/0001
        f3       chrA:3   sub(A->G) 1/1
        """), {
        "denovo_location": "location",
        "denovo_variant": "variant",
        "denovo_family_id": "familyId",
        "denovo_best_state": "bestState",
    }),
    (textwrap.dedent("""
        familyId chrom pos ref alt bestState
        f1       chrA  1   A   G   22121/00101
        f2       chrA  2   A   G   2221/0001
        f3       chrA  3   A   G   1/1
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
        f1       chrA  1   A   G   f1.s1,f1.s2
        f2       chrA  2   A   G   f2.s1
        f3       chrA  3   A   G   f3.p1
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
        f1       chrA  1   A   G   f1.s1;f1.s2
        f2       chrA  2   A   G   f2.s1
        f3       chrA  3   A   G   f3.p1
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
    variants: str, params: dict[str, str]
) -> None:
    gpf = alla_gpf(tmp_path)
    denovo_path = setup_denovo(tmp_path / "variants.tsv", variants)

    variants_loader = DenovoLoader(
        families_fixture, str(denovo_path),
        genome=gpf.reference_genome, params=params,
        sort=False
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
