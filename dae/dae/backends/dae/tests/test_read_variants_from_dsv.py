import pytest
import pandas as pd
import numpy as np
from dae.backends.dae.loader import RawDaeLoader

from dae.utils.vcf_utils import GENOTYPE_TYPE

from .conftest import relative_to_this_folder


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
    output = RawDaeLoader.produce_genotype(
        fake_families.families['f1'], ['f1.p1', 'f1.s2'])
    assert np.array_equal(output, expected_output)
    assert output.dtype == GENOTYPE_TYPE


def test_produce_genotype_no_people_with_variants(fake_families):
    expected_output = np.array([[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]])
    output = RawDaeLoader.produce_genotype(fake_families.families['f1'], [])
    assert np.array_equal(output, expected_output)
    assert output.dtype == GENOTYPE_TYPE


def test_families_instance_type_assertion():
    error_message = 'families must be an instance of FamiliesData!'
    with pytest.raises(AssertionError) as excinfo:
        RawDaeLoader.flexible_denovo_read(
            None, None, location='foo', variant='bar',
            personId='baz', families='bla')
    assert str(excinfo.value) == error_message


def test_read_variants_DAE_style(default_genome):
    filename = relative_to_this_folder('fixtures/variants_DAE_style.tsv')
    res_df = RawDaeLoader.flexible_denovo_read(
        filename, default_genome, location='location', variant='variant',
        familyId='familyId', bestSt='bestState'
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


def test_read_variants_a_la_VCF_style():
    filename = relative_to_this_folder('fixtures/variants_VCF_style.tsv')
    res_df = RawDaeLoader.flexible_denovo_read(
        filename, None, chrom='chrom', pos='pos',
        ref='ref', alt='alt', familyId='familyId', bestSt='bestState'
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


def test_read_variants_mixed_A():
    filename = relative_to_this_folder('fixtures/variants_mixed_style_A.tsv')
    res_df = RawDaeLoader.flexible_denovo_read(
        filename, None, location='location',
        ref='ref', alt='alt', familyId='familyId', bestSt='bestState'
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


def test_read_variants_mixed_B(default_genome):
    filename = relative_to_this_folder('fixtures/variants_mixed_style_B.tsv')
    res_df = RawDaeLoader.flexible_denovo_read(
        filename, default_genome, chrom='chrom', pos='pos',
        variant='variant', familyId='familyId', bestSt='bestState'
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
    ('fixtures/variants_personId_single.tsv'),
    ('fixtures/variants_personId_list.tsv'),
])
def test_read_variants_person_ids(filename, fake_families):
    filename = relative_to_this_folder(filename)
    res_df = RawDaeLoader.flexible_denovo_read(
        filename, None, chrom='chrom', pos='pos',
        ref='ref', alt='alt', personId='personId', families=fake_families
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


def test_read_variants_different_separator():
    filename = relative_to_this_folder(
        'fixtures/variants_different_separator.dsv'
    )
    res_df = RawDaeLoader.flexible_denovo_read(
        filename, None, sep='$', chrom='chrom', pos='pos',
        ref='ref', alt='alt', familyId='familyId', bestSt='bestState'
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


def test_read_variants_genome_assertion():
    filename = relative_to_this_folder('fixtures/variants_DAE_style.tsv')

    with pytest.raises(AssertionError) as excinfo:
        RawDaeLoader.flexible_denovo_read(
            filename, None, location='location', variant='variant',
            familyId='familyId', bestSt='bestState'
        )

    assert str(excinfo.value) == 'You must provide a genome object!'
