import pytest
import pandas as pd
import numpy as np

from dae.pedigrees.family import PedigreeReader
from dae.pedigrees.family import FamiliesData

from dae.backends.dae.loader import DenovoLoader

from dae.utils.variant_utils import GENOTYPE_TYPE


@pytest.fixture(scope='session')
def fake_families(fixture_dirname):
    ped_df = PedigreeReader.flexible_pedigree_read(
        fixture_dirname('denovo_import/fake_pheno.ped')
    )
    fake_families = FamiliesData.from_pedigree_df(ped_df)
    return fake_families


def compare_variant_dfs(res_df, expected_df):
    equal = True

    # The genotype column must be compared separately
    # since it contains numpy arrays
    res_genotype = res_df.loc[:, 'genotype']
    expected_genotype = res_df.loc[:, 'genotype']
    del(res_df['genotype'])
    del(expected_df['genotype'])

    equal = equal and res_df.equals(expected_df)
    equal = equal and len(res_genotype) == len(expected_genotype)
    for i in range(0, len(res_genotype)):
        equal = equal and np.array_equal(
            res_genotype[i],
            expected_genotype[i]
        )
    return equal


def test_produce_genotype(fake_families):
    expected_output = np.array([[0, 0, 0, 0, 0], [0, 0, 0, 1, 1]])
    output = DenovoLoader.produce_genotype(
        fake_families.families['f1'], ['f1.p1', 'f1.s2'])
    assert np.array_equal(output, expected_output)
    assert output.dtype == GENOTYPE_TYPE


def test_produce_genotype_no_people_with_variants(fake_families):
    expected_output = np.array([[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]])
    output = DenovoLoader.produce_genotype(fake_families.families['f1'], [])
    assert np.array_equal(output, expected_output)
    assert output.dtype == GENOTYPE_TYPE


def test_families_instance_type_assertion():
    error_message = 'families must be an instance of FamiliesData!'
    with pytest.raises(AssertionError) as excinfo:
        DenovoLoader.flexible_denovo_load(
            None, None, denovo_location='foo', denovo_variant='bar',
            denovo_person_id='baz', families='bla')
    assert str(excinfo.value) == error_message


def test_read_variants_DAE_style(default_genome, fixture_dirname, fake_families):
    filename = fixture_dirname('denovo_import/variants_DAE_style.tsv')
    res_df = DenovoLoader.flexible_denovo_load(
        filename, default_genome, families=fake_families,
        denovo_location='location',
        denovo_variant='variant',
        denovo_family_id='familyId', denovo_best_state='bestState'
    )

    expected_df = pd.DataFrame({
        'chrom': ['1', '2', '2'],
        'position': [123, 234, 234],
        'reference': ['A', 'T', 'G'],
        'alternative': ['G', 'T', 'A'],
        'family_id': ['f1', 'f1', 'f2'],
        'genotype': [
            np.array([[0, 0, 0, 0, 0], [0, 0, 1, 0, 1]]),
            np.array([[0, 0, 0, 0, 0], [0, 0, 1, 0, 0]]),
            np.array([[0, 0, 0, 0], [0, 0, 0, 1]]),
        ],
    })

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_a_la_VCF_style(fixture_dirname, fake_families):
    filename = fixture_dirname('denovo_import/variants_VCF_style.tsv')
    res_df = DenovoLoader.flexible_denovo_load(
        filename, None,  families=fake_families,
        denovo_chrom='chrom', denovo_pos='pos',
        denovo_ref='ref',
        denovo_alt='alt', denovo_family_id='familyId',
        denovo_best_state='bestState'
    )

    expected_df = pd.DataFrame({
        'chrom': ['1', '2', '2'],
        'position': [123, 234, 234],
        'reference': ['A', 'T', 'G'],
        'alternative': ['G', 'T', 'A'],
        'family_id': ['f1', 'f1', 'f2'],
        'genotype': [
            np.array([[0, 0, 0, 0, 0], [0, 0, 1, 0, 1]]),
            np.array([[0, 0, 0, 0, 0], [0, 0, 1, 0, 0]]),
            np.array([[0, 0, 0, 0], [0, 0, 0, 1]]),
        ],
    })

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_mixed_A(fixture_dirname, fake_families):
    filename = fixture_dirname('denovo_import/variants_mixed_style_A.tsv')
    res_df = DenovoLoader.flexible_denovo_load(
        filename, None,  families=fake_families,
        denovo_location='location',
        denovo_ref='ref',
        denovo_alt='alt', denovo_family_id='familyId',
        denovo_best_state='bestState'
    )

    expected_df = pd.DataFrame({
        'chrom': ['1', '2', '2'],
        'position': [123, 234, 234],
        'reference': ['A', 'T', 'G'],
        'alternative': ['G', 'T', 'A'],
        'family_id': ['f1', 'f1', 'f2'],
        'genotype': [
            np.array([[0, 0, 0, 0, 0], [0, 0, 1, 0, 1]]),
            np.array([[0, 0, 0, 0, 0], [0, 0, 1, 0, 0]]),
            np.array([[0, 0, 0, 0], [0, 0, 0, 1]]),
        ],
    })

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_mixed_B(default_genome, fixture_dirname, fake_families):
    filename = fixture_dirname('denovo_import/variants_mixed_style_B.tsv')
    res_df = DenovoLoader.flexible_denovo_load(
        filename, default_genome,  families=fake_families,
        denovo_chrom='chrom', denovo_pos='pos',
        denovo_variant='variant',
        denovo_family_id='familyId', denovo_best_state='bestState'
    )

    expected_df = pd.DataFrame({
        'chrom': ['1', '2', '2'],
        'position': [123, 234, 234],
        'reference': ['A', 'T', 'G'],
        'alternative': ['G', 'T', 'A'],
        'family_id': ['f1', 'f1', 'f2'],
        'genotype': [
            np.array([[0, 0, 0, 0, 0], [0, 0, 1, 0, 1]]),
            np.array([[0, 0, 0, 0, 0], [0, 0, 1, 0, 0]]),
            np.array([[0, 0, 0, 0], [0, 0, 0, 1]]),
        ],
    })

    assert compare_variant_dfs(res_df, expected_df)


@pytest.mark.parametrize('filename', [
    ('denovo_import/variants_personId_single.tsv'),
    ('denovo_import/variants_personId_list.tsv'),
])
def test_read_variants_person_ids(filename, fake_families, fixture_dirname):
    filename = fixture_dirname(filename)
    res_df = DenovoLoader.flexible_denovo_load(
        filename, None,  families=fake_families,
        denovo_chrom='chrom', denovo_pos='pos',
        denovo_ref='ref', denovo_alt='alt', denovo_person_id='personId'
    )

    expected_df = pd.DataFrame({
        'chrom': ['1', '2', '2'],
        'position': [123, 234, 234],
        'reference': ['A', 'T', 'G'],
        'alternative': ['G', 'T', 'A'],
        'family_id': ['f1', 'f1', 'f2'],
        'genotype': [
            np.array([[0, 0, 0, 0, 0], [0, 0, 1, 0, 1]]),
            np.array([[0, 0, 0, 0, 0], [0, 0, 1, 0, 0]]),
            np.array([[0, 0, 0, 0], [0, 0, 0, 1]]),
        ],
    })

    res_df = res_df.sort_values(['position', 'reference'])
    res_df = res_df.reset_index(drop=True)
    expected_df = expected_df.sort_values(['position', 'reference'])
    expected_df = expected_df.reset_index(drop=True)

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_different_separator(fixture_dirname, fake_families):
    filename = fixture_dirname(
        'denovo_import/variants_different_separator.dsv')
    res_df = DenovoLoader.flexible_denovo_load(
        filename, None,  families=fake_families,
        denovo_sep='$', denovo_chrom='chrom',
        denovo_pos='pos',
        denovo_ref='ref',
        denovo_alt='alt', denovo_family_id='familyId',
        denovo_best_state='bestState'
    )

    expected_df = pd.DataFrame({
        'chrom': ['1', '2', '2'],
        'position': [123, 234, 234],
        'reference': ['A', 'T', 'G'],
        'alternative': ['G', 'T', 'A'],
        'family_id': ['f1', 'f1', 'f2'],
        'genotype': [
            np.array([[0, 0, 0, 0, 0], [0, 0, 1, 0, 1]]),
            np.array([[0, 0, 0, 0, 0], [0, 0, 1, 0, 0]]),
            np.array([[0, 0, 0, 0], [0, 0, 0, 1]]),
        ],
    })

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_genome_assertion(fixture_dirname, fake_families):
    filename = fixture_dirname('denovo_import/variants_DAE_style.tsv')

    with pytest.raises(AssertionError) as excinfo:
        DenovoLoader.flexible_denovo_load(
            filename, None,  families=fake_families,
            denovo_location='location',
            denovo_variant='variant',
            denovo_family_id='familyId', denovo_best_state='bestState'
        )

    assert str(excinfo.value) == 'You must provide a genome object!'
