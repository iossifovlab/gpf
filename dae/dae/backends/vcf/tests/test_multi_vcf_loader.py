import pytest
import os
import numpy as np
from dae.backends.vcf.loader import VcfLoader, MultiVcfLoader
from dae.pedigrees.family import PedigreeReader
from dae.pedigrees.family import FamiliesData


@pytest.mark.parametrize('multivcf_files', [
    [
        'multivcf_split1.vcf',
        'multivcf_split2.vcf'
    ],
    [
        'multivcf_original.vcf'
    ]
])
def test_multivcf_loader(fixture_dirname, multivcf_files):
    ped_file = fixture_dirname('backends/multivcf.ped')
    single_vcf = fixture_dirname('backends/multivcf_original.vcf')

    multivcf_files = list(map(
        lambda x: os.path.join(fixture_dirname('backends'), x), multivcf_files
    ))

    ped_df = PedigreeReader.flexible_pedigree_read(ped_file)
    families = FamiliesData.from_pedigree_df(ped_df)
    families_multi = FamiliesData.from_pedigree_df(ped_df)

    single_loader = VcfLoader(families, single_vcf)
    assert single_loader is not None
    multi_vcf_loader = MultiVcfLoader(families_multi, multivcf_files, False)
    assert multi_vcf_loader is not None
    single_it = single_loader.summary_genotypes_iterator()
    multi_it = multi_vcf_loader.summary_genotypes_iterator()
    for s, m in zip(single_it, multi_it):
        assert s[0] == m[0]

        s_gt_f1 = s[1].get_family_genotype(families.get_family('f1'))
        m_gt_f1 = m[1].get_family_genotype(families_multi.get_family('f1'))
        assert all((s_gt_f1 == m_gt_f1).flatten())

        s_gt_f2 = s[1].get_family_genotype(families.get_family('f2'))
        m_gt_f2 = m[1].get_family_genotype(families_multi.get_family('f2'))
        assert all((s_gt_f2 == m_gt_f2).flatten())

        s_gt_f3 = s[1].get_family_genotype(families.get_family('f3'))
        m_gt_f3 = m[1].get_family_genotype(families_multi.get_family('f3'))
        assert all((s_gt_f3 == m_gt_f3).flatten())

        s_gt_f4 = s[1].get_family_genotype(families.get_family('f4'))
        m_gt_f4 = m[1].get_family_genotype(families_multi.get_family('f4'))
        assert all((s_gt_f4 == m_gt_f4).flatten())

        s_gt_f5 = s[1].get_family_genotype(families.get_family('f5'))
        m_gt_f5 = m[1].get_family_genotype(families_multi.get_family('f5'))
        assert all((s_gt_f5 == m_gt_f5).flatten())


def test_multivcf_loader_fill_missing_ref(fixture_dirname):
    ped_file = fixture_dirname('backends/multivcf.ped')

    multivcf_files = [
        fixture_dirname('backends/multivcf_missing1.vcf'),
        fixture_dirname('backends/multivcf_missing2.vcf'),
    ]
    ped_df = PedigreeReader.flexible_pedigree_read(ped_file)
    families = FamiliesData.from_pedigree_df(ped_df)

    multi_vcf_loader = MultiVcfLoader(families, multivcf_files, False)
    assert multi_vcf_loader is not None
    multi_it = multi_vcf_loader.summary_genotypes_iterator()
    first_present = next(multi_it)
    second_missing = next(multi_it)
    # print(second_missing[1].full_families_genotypes())
    next(multi_it)
    next(multi_it)
    next(multi_it)
    next(multi_it)
    assert next(multi_it, None) is None

    gt1_f1 = first_present[1].get_family_genotype(
        multi_vcf_loader.families.get_family('f1'))
    gt1_f1_expected = np.array([
        [1, 0, 0, 0],
        [1, 0, 1, 1]
    ], dtype=np.int8)
    gt1_f5 = first_present[1].get_family_genotype(
        multi_vcf_loader.families.get_family('f5'))
    gt1_f5_expected = np.array([
        [1, 0, 1, 0],
        [1, 0, 0, 1]
    ], dtype=np.int8)

    assert all((gt1_f1 == gt1_f1_expected).flatten())
    assert all((gt1_f5 == gt1_f5_expected).flatten())

    gt2_f1 = second_missing[1].get_family_genotype(families.get_family('f1'))
    gt2_f2 = second_missing[1].get_family_genotype(families.get_family('f2'))
    gt2_f3 = second_missing[1].get_family_genotype(families.get_family('f3'))
    gt2_f5 = second_missing[1].get_family_genotype(families.get_family('f5'))

    gt2_f1_f2_f3_expected = np.array([[0]*4]*2, dtype=np.int8)
    gt2_f5_expected = np.array([
        [0, 1, 1, 0],
        [0, 1, 0, 1]
    ], dtype=np.int8)

    assert all((gt2_f1 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f2 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f3 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f5 == gt2_f5_expected).flatten())


def test_multivcf_loader_fill_missing_unknown(fixture_dirname):
    ped_file = fixture_dirname('backends/multivcf.ped')

    multivcf_files = [
        fixture_dirname('backends/multivcf_missing1.vcf'),
        fixture_dirname('backends/multivcf_missing2.vcf'),
    ]
    ped_df = PedigreeReader.flexible_pedigree_read(ped_file)
    families = FamiliesData.from_pedigree_df(ped_df)

    multi_vcf_loader = MultiVcfLoader(families, multivcf_files, True)
    assert multi_vcf_loader is not None
    multi_it = multi_vcf_loader.summary_genotypes_iterator()
    first_present = next(multi_it)
    second_missing = next(multi_it)
    # print(second_missing[1].full_families_genotypes())
    next(multi_it)
    next(multi_it)
    next(multi_it)
    next(multi_it)
    assert next(multi_it, None) is None

    gt1_f1 = first_present[1].get_family_genotype(
        multi_vcf_loader.families.get_family('f1'))
    gt1_f1_expected = np.array([
        [1, 0, 0, 0],
        [1, 0, 1, 1]
    ], dtype=np.int8)
    gt1_f5 = first_present[1].get_family_genotype(
        multi_vcf_loader.families.get_family('f5'))
    gt1_f5_expected = np.array([
        [1, 0, 1, 0],
        [1, 0, 0, 1]
    ], dtype=np.int8)

    assert all((gt1_f1 == gt1_f1_expected).flatten())
    assert all((gt1_f5 == gt1_f5_expected).flatten())

    gt2_f1 = second_missing[1].get_family_genotype(families.get_family('f1'))
    gt2_f2 = second_missing[1].get_family_genotype(families.get_family('f2'))
    gt2_f3 = second_missing[1].get_family_genotype(families.get_family('f3'))
    gt2_f5 = second_missing[1].get_family_genotype(families.get_family('f5'))

    gt2_f1_f2_f3_expected = np.array([[-1]*4]*2, dtype=np.int8)
    gt2_f5_expected = np.array([
        [0, 1, 1, 0],
        [0, 1, 0, 1]
    ], dtype=np.int8)

    assert all((gt2_f1 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f2 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f3 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f5 == gt2_f5_expected).flatten())
