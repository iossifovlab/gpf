import pytest
import os
import numpy as np
from dae.backends.vcf.loader import VcfLoader, MultiVcfLoader
from dae.pedigrees.loader import FamiliesLoader


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

    families = FamiliesLoader(ped_file).load()
    families_multi = FamiliesLoader(ped_file).load()

    single_loader = VcfLoader(families, single_vcf)
    assert single_loader is not None
    multi_vcf_loader = MultiVcfLoader(families_multi, multivcf_files, False)
    assert multi_vcf_loader is not None
    single_it = single_loader.summary_genotypes_iterator()
    multi_it = multi_vcf_loader.summary_genotypes_iterator()
    for s, m in zip(single_it, multi_it):
        assert s[0] == m[0]

        s_gt_f1 = s[1].get_family_genotype(families.get('f1'))
        m_gt_f1 = m[1].get_family_genotype(families_multi.get('f1'))
        assert all((s_gt_f1 == m_gt_f1).flatten())

        s_gt_f2 = s[1].get_family_genotype(families.get('f2'))
        m_gt_f2 = m[1].get_family_genotype(families_multi.get('f2'))
        assert all((s_gt_f2 == m_gt_f2).flatten())

        s_gt_f3 = s[1].get_family_genotype(families.get('f3'))
        m_gt_f3 = m[1].get_family_genotype(families_multi.get('f3'))
        assert all((s_gt_f3 == m_gt_f3).flatten())

        s_gt_f4 = s[1].get_family_genotype(families.get('f4'))
        m_gt_f4 = m[1].get_family_genotype(families_multi.get('f4'))
        assert all((s_gt_f4 == m_gt_f4).flatten())

        s_gt_f5 = s[1].get_family_genotype(families.get('f5'))
        m_gt_f5 = m[1].get_family_genotype(families_multi.get('f5'))
        assert all((s_gt_f5 == m_gt_f5).flatten())


@pytest.mark.parametrize('fill_flag, fill_value', [[True, 0], [False, -1]])
def test_multivcf_loader_fill_missing(fixture_dirname, fill_flag, fill_value):
    ped_file = fixture_dirname('backends/multivcf.ped')

    multivcf_files = [
        fixture_dirname('backends/multivcf_missing1.vcf'),
        fixture_dirname('backends/multivcf_missing2.vcf'),
    ]
    families = FamiliesLoader(ped_file).load()

    multi_vcf_loader = MultiVcfLoader(families, multivcf_files, fill_flag)
    assert multi_vcf_loader is not None
    multi_it = multi_vcf_loader.summary_genotypes_iterator()
    sum_gts = [sum_gt for sum_gt in multi_it]
    first_present = sum_gts[0]
    second_missing = sum_gts[1]
    assert next(multi_it, None) is None

    gt1_f1 = first_present[1].get_family_genotype(
        multi_vcf_loader.families.get('f1'))
    gt1_f1_expected = np.array([
        [1, 0, 0, 0],
        [1, 0, 1, 1]
    ], dtype=np.int8)
    gt1_f5 = first_present[1].get_family_genotype(
        multi_vcf_loader.families.get('f5'))
    gt1_f5_expected = np.array([
        [1, 0, 1, 0],
        [1, 0, 0, 1]
    ], dtype=np.int8)

    assert all((gt1_f1 == gt1_f1_expected).flatten())
    assert all((gt1_f5 == gt1_f5_expected).flatten())

    gt2_f1 = second_missing[1].get_family_genotype(families.get('f1'))
    gt2_f2 = second_missing[1].get_family_genotype(families.get('f2'))
    gt2_f3 = second_missing[1].get_family_genotype(families.get('f3'))
    gt2_f5 = second_missing[1].get_family_genotype(families.get('f5'))

    gt2_f1_f2_f3_expected = np.array([[fill_value]*4]*2, dtype=np.int8)
    gt2_f5_expected = np.array([
        [0, 1, 1, 0],
        [0, 1, 0, 1]
    ], dtype=np.int8)

    assert all((gt2_f1 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f2 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f3 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f5 == gt2_f5_expected).flatten())
    assert(sum_gts[0][0].ref_allele.position == 865582)
    assert(sum_gts[1][0].ref_allele.position == 865583)
    assert(sum_gts[2][0].ref_allele.position == 865624)
    assert(sum_gts[3][0].ref_allele.position == 865627)
    assert(sum_gts[4][0].ref_allele.position == 865664)
    assert(sum_gts[5][0].ref_allele.position == 865691)
