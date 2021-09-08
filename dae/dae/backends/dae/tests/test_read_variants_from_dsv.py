import pytest
import pandas as pd
import numpy as np

from dae.variants.attributes import Inheritance

from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.family import FamiliesData

from dae.backends.dae.loader import DenovoLoader

from dae.utils.variant_utils import GENOTYPE_TYPE


@pytest.fixture(scope="session")
def fake_families(fixture_dirname):
    ped_df = FamiliesLoader.flexible_pedigree_read(
        fixture_dirname("denovo_import/fake_pheno.ped")
    )
    fake_families = FamiliesData.from_pedigree_df(ped_df)
    return fake_families


def compare_variant_dfs(res_df, expected_df):
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


def test_produce_genotype(fake_families, genome_2013):
    expected_output = np.array([[0, 0, 0, 0, 0], [0, 0, 0, 1, 1]])
    output = DenovoLoader.produce_genotype(
        "1", 123123, genome_2013, fake_families["f1"], ["f1.p1", "f1.s2"]
    )
    assert np.array_equal(output, expected_output)
    assert output.dtype == GENOTYPE_TYPE


def test_produce_genotype_no_people_with_variants(fake_families, genome_2013):
    expected_output = np.array([[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]])
    output = DenovoLoader.produce_genotype(
        "1", 123123, genome_2013, fake_families["f1"], []
    )
    assert np.array_equal(output, expected_output)
    assert output.dtype == GENOTYPE_TYPE


def test_families_instance_type_assertion():
    error_message = "families must be an instance of FamiliesData!"
    with pytest.raises(AssertionError) as excinfo:
        DenovoLoader.flexible_denovo_load(
            None,
            None,
            denovo_location="foo",
            denovo_variant="bar",
            denovo_person_id="baz",
            families="bla",
        )
    assert str(excinfo.value) == error_message


def test_read_variants_DAE_style(genome_2013, fixture_dirname, fake_families):
    filename = fixture_dirname("denovo_import/variants_DAE_style.tsv")
    res_df = DenovoLoader.flexible_denovo_load(
        filename,
        genome_2013,
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


def test_read_variants_a_la_VCF_style(
    genome_2013, fixture_dirname, fake_families
):
    filename = fixture_dirname("denovo_import/variants_VCF_style.tsv")
    res_df = DenovoLoader.flexible_denovo_load(
        filename,
        genome_2013,
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


def test_read_variants_mixed_A(genome_2013, fixture_dirname, fake_families):
    filename = fixture_dirname("denovo_import/variants_mixed_style_A.tsv")
    res_df = DenovoLoader.flexible_denovo_load(
        filename,
        genome_2013,
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


def test_read_variants_mixed_B(genome_2013, fixture_dirname, fake_families):
    filename = fixture_dirname("denovo_import/variants_mixed_style_B.tsv")
    res_df = DenovoLoader.flexible_denovo_load(
        filename,
        genome_2013,
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
    genome_2013, filename, fake_families, fixture_dirname
):
    filename = fixture_dirname(filename)
    res_df = DenovoLoader.flexible_denovo_load(
        filename,
        genome_2013,
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
    genome_2013, fixture_dirname, fake_families
):
    filename = fixture_dirname(
        "denovo_import/variants_different_separator.dsv"
    )
    res_df = DenovoLoader.flexible_denovo_load(
        filename,
        genome_2013,
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
    genome_2013, fixture_dirname, fake_families
):
    filename = fixture_dirname(
        "denovo_import/variants_VCF_genotype.tsv"
    )
    res_df = DenovoLoader.flexible_denovo_load(
        filename,
        genome_2013,
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


def test_read_variants_genome_assertion(fixture_dirname, fake_families):
    filename = fixture_dirname("denovo_import/variants_DAE_style.tsv")

    with pytest.raises(AssertionError) as excinfo:
        DenovoLoader.flexible_denovo_load(
            filename,
            None,
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
    genome_2013, fixture_dirname, fake_families, filename, params
):
    denovo_filename = fixture_dirname(f"denovo_import/{filename}")
    variants_loader = DenovoLoader(
        fake_families, denovo_filename, 
        genome=genome_2013.get_genomic_sequence(), params=params
    )

    vs = list(variants_loader.full_variants_iterator())
    print(vs)

    def falt_allele(index):
        return vs[index][1][0].alt_alleles[0]

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
    genome_2013, fixture_dirname, fake_families,
):
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
        genome=genome_2013.get_genomic_sequence(), params=params
    )

    vs = variants_loader.full_variants_iterator()

    svs = []
    fvs = []
    for sv, fvs_ in vs:
        print(sv, fvs)
        svs.append(sv)
        for fv in fvs_:
            fvs.append(fv)

    assert len(svs) == 3
    assert len(fvs) == 4
