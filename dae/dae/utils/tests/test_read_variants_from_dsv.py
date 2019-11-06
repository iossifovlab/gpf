import pytest
import pandas as pd
import numpy as np
from dae.utils.helpers import produce_genotype, read_variants_from_dsv
from dae.variants.family import FamiliesBase
from dae.utils.vcf_utils import GENOTYPE_TYPE

from dae.utils.tests.conftest import relative_to_this_folder


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
    expected_output = np.array([0, 0, 0, 0, 0, 0, 0, 1, 0, 1])
    output = produce_genotype(fake_families.families['f1'], ['f1.p1', 'f1.s2'])
    assert np.array_equal(output, expected_output)
    assert output.dtype == GENOTYPE_TYPE


def test_produce_genotype_no_people_with_variants(fake_families):
    expected_output = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    output = produce_genotype(fake_families.families['f1'], [])
    assert np.array_equal(output, expected_output)
    assert output.dtype == GENOTYPE_TYPE


def test_read_variants_column_assertion_location():
    """
    Tests the assertion for having either a location or CHROM and POS
    columns.
    """

    error_message = ('You must specify either a location column or'
                     ' chromosome and position columns!')
    with pytest.raises(AssertionError) as excinfo:
        read_variants_from_dsv(
            None, None, variant='foo', familyId='bar', genotype='baz')
    assert str(excinfo.value) == error_message

    with pytest.raises(AssertionError) as excinfo:
        read_variants_from_dsv(
            None, None, variant='foo', chrom='CHROM',
            familyId='bar', genotype='baz')
    assert str(excinfo.value) == error_message

    with pytest.raises(AssertionError) as excinfo:
        read_variants_from_dsv(
            None, None, variant='foo', pos='POS',
            familyId='bar', genotype='baz')
    assert str(excinfo.value) == error_message


def test_read_variants_column_assertion_variant():
    """
    Tests the assertion for having either a variant or REF and ALT
    columns.
    """

    error_message = ('You must specify either a variant column or'
                     ' reference and alternative columns!')
    with pytest.raises(AssertionError) as excinfo:
        read_variants_from_dsv(
            None, None, location='foo', familyId='bar', genotype='baz')
    assert str(excinfo.value) == error_message

    with pytest.raises(AssertionError) as excinfo:
        read_variants_from_dsv(
            None, None, location='foo', ref='REF',
            familyId='bar', genotype='baz')
    assert str(excinfo.value) == error_message

    with pytest.raises(AssertionError) as excinfo:
        read_variants_from_dsv(
            None, None, location='foo', alt='ALT',
            familyId='bar', genotype='baz')
    assert str(excinfo.value) == error_message


def test_read_variants_column_assertion_family():
    """
    Tests the assertion for having either a personId column with a
    FamiliesBase object specified or familyId and genotype columns.
    """

    error_message = ('You must specify either a personId column and'
                     ' provide a FamiliesBase object or specify'
                     ' familyId and genotype columns!')
    with pytest.raises(AssertionError) as excinfo:
        read_variants_from_dsv(
            None, None, location='foo', variant='bar')
    assert str(excinfo.value) == error_message

    with pytest.raises(AssertionError) as excinfo:
        read_variants_from_dsv(
            None, None, location='foo', variant='bar',
            familyId='baz')
    assert str(excinfo.value) == error_message

    with pytest.raises(AssertionError) as excinfo:
        read_variants_from_dsv(
            None, None, location='foo', variant='bar',
            genotype='baz')
    assert str(excinfo.value) == error_message

    with pytest.raises(AssertionError) as excinfo:
        read_variants_from_dsv(
            None, None, location='foo', variant='bar',
            personId='baz')
    assert str(excinfo.value) == error_message

    with pytest.raises(AssertionError) as excinfo:
        read_variants_from_dsv(
            None, None, location='foo', variant='bar',
            families=FamiliesBase())
    assert str(excinfo.value) == error_message


def test_families_instance_type_assertion():
    error_message = 'families must be an instance of FamiliesBase!'
    with pytest.raises(AssertionError) as excinfo:
        read_variants_from_dsv(
            None, None, location='foo', variant='bar',
            personId='baz', families='bla')
    assert str(excinfo.value) == error_message


def test_read_variants_DAE_style(default_genome):
    filename = relative_to_this_folder('fixtures/variants_DAE_style.tsv')
    res_df = read_variants_from_dsv(
        filename, default_genome, location='location', variant='variant',
        familyId='familyId', genotype='bestState'
    )

    expected_df = pd.DataFrame({
        'chrom': ['1', '2', '2'],
        'position': ['123', '234', '234'],
        'reference': ['A', 'T', 'G'],
        'alternative': ['G', 'T', 'A'],
        'family_id': ['f1', 'f1', 'f2'],
        'genotype': [
            np.array([0, 0, 0, 0, 0, 0, 0, 1, 0, 1]),
            np.array([0, 0, 0, 0, 0, 0, 0, 1, 0, 0]),
            np.array([0, 0, 0, 0, 0, 0, 0, 1]),
        ],
    })

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_a_la_VCF_style():
    filename = relative_to_this_folder('fixtures/variants_VCF_style.tsv')
    res_df = read_variants_from_dsv(
        filename, None, chrom='chrom', pos='pos',
        ref='ref', alt='alt', familyId='familyId', genotype='bestState'
    )

    expected_df = pd.DataFrame({
        'chrom': ['1', '2', '2'],
        'position': ['123', '234', '234'],
        'reference': ['A', 'T', 'G'],
        'alternative': ['G', 'T', 'A'],
        'family_id': ['f1', 'f1', 'f2'],
        'genotype': [
            np.array([0, 0, 0, 0, 0, 0, 0, 1, 0, 1]),
            np.array([0, 0, 0, 0, 0, 0, 0, 1, 0, 0]),
            np.array([0, 0, 0, 0, 0, 0, 0, 1]),
        ],
    })

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_mixed_A():
    filename = relative_to_this_folder('fixtures/variants_mixed_style_A.tsv')
    res_df = read_variants_from_dsv(
        filename, None, location='location',
        ref='ref', alt='alt', familyId='familyId', genotype='bestState'
    )

    expected_df = pd.DataFrame({
        'chrom': ['1', '2', '2'],
        'position': ['123', '234', '234'],
        'reference': ['A', 'T', 'G'],
        'alternative': ['G', 'T', 'A'],
        'family_id': ['f1', 'f1', 'f2'],
        'genotype': [
            np.array([0, 0, 0, 0, 0, 0, 0, 1, 0, 1]),
            np.array([0, 0, 0, 0, 0, 0, 0, 1, 0, 0]),
            np.array([0, 0, 0, 0, 0, 0, 0, 1]),
        ],
    })

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_mixed_B(default_genome):
    filename = relative_to_this_folder('fixtures/variants_mixed_style_B.tsv')
    res_df = read_variants_from_dsv(
        filename, default_genome, chrom='chrom', pos='pos',
        variant='variant', familyId='familyId', genotype='bestState'
    )

    expected_df = pd.DataFrame({
        'chrom': ['1', '2', '2'],
        'position': ['123', '234', '234'],
        'reference': ['A', 'T', 'G'],
        'alternative': ['G', 'T', 'A'],
        'family_id': ['f1', 'f1', 'f2'],
        'genotype': [
            np.array([0, 0, 0, 0, 0, 0, 0, 1, 0, 1]),
            np.array([0, 0, 0, 0, 0, 0, 0, 1, 0, 0]),
            np.array([0, 0, 0, 0, 0, 0, 0, 1]),
        ],
    })

    assert compare_variant_dfs(res_df, expected_df)


@pytest.mark.parametrize('filename', [
    ('fixtures/variants_personId_single.tsv'),
    ('fixtures/variants_personId_list.tsv'),
])
def test_read_variants_person_ids(filename, fake_families):
    filename = relative_to_this_folder(filename)
    res_df = read_variants_from_dsv(
        filename, None, chrom='chrom', pos='pos',
        ref='ref', alt='alt', personId='personId', families=fake_families
    )

    expected_df = pd.DataFrame({
        'chrom': ['1', '2', '2'],
        'position': ['123', '234', '234'],
        'reference': ['A', 'T', 'G'],
        'alternative': ['G', 'T', 'A'],
        'family_id': ['f1', 'f1', 'f2'],
        'genotype': [
            np.array([0, 0, 0, 0, 0, 0, 0, 1, 0, 1]),
            np.array([0, 0, 0, 0, 0, 0, 0, 1, 0, 0]),
            np.array([0, 0, 0, 0, 0, 0, 0, 1]),
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
    res_df = read_variants_from_dsv(
        filename, None, sep='$', chrom='chrom', pos='pos',
        ref='ref', alt='alt', familyId='familyId', genotype='bestState'
    )

    expected_df = pd.DataFrame({
        'chrom': ['1', '2', '2'],
        'position': ['123', '234', '234'],
        'reference': ['A', 'T', 'G'],
        'alternative': ['G', 'T', 'A'],
        'family_id': ['f1', 'f1', 'f2'],
        'genotype': [
            np.array([0, 0, 0, 0, 0, 0, 0, 1, 0, 1]),
            np.array([0, 0, 0, 0, 0, 0, 0, 1, 0, 0]),
            np.array([0, 0, 0, 0, 0, 0, 0, 1]),
        ],
    })

    assert compare_variant_dfs(res_df, expected_df)


def test_read_variants_genome_assertion():
    filename = relative_to_this_folder('fixtures/variants_DAE_style.tsv')

    with pytest.raises(AssertionError) as excinfo:
        res_df = read_variants_from_dsv(
            filename, None, location='location', variant='variant',
            familyId='familyId', genotype='bestState'
        )
        
    assert str(excinfo.value) == 'You must provide a genome object!'
