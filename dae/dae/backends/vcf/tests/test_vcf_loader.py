import pytest
import os
import numpy as np
from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.family import FamiliesData

from dae.backends.vcf.loader import VcfLoader
from dae.utils.variant_utils import GENOTYPE_TYPE


@pytest.mark.parametrize("fixture_data", [
    "backends/effects_trio_dad",
    "backends/effects_trio",
    "backends/trios2",
    "backends/members_in_order1",
    "backends/members_in_order2",
    "backends/unknown_trio",
    "backends/trios_multi",
    "backends/quads_f1",
])
def test_vcf_loader(vcf_loader_data, variants_vcf, fixture_data):
    conf = vcf_loader_data(fixture_data)
    print(conf)

    fvars = variants_vcf(fixture_data)

    ped_df = FamiliesLoader.flexible_pedigree_read(conf.pedigree)
    families = FamiliesData.from_pedigree_df(ped_df)

    loader = VcfLoader(families, [conf.vcf], params={
        'vcf_include_reference_genotypes': True,
        'vcf_include_unknown_family_genotypes': True,
        'vcf_include_unknown_person_genotypes': True
    })
    assert loader is not None

    vars_old = list(fvars.query_variants(
        return_reference=True, return_unknown=True))
    vars_new = list(loader.family_variants_iterator())

    for nfv, ofv in zip(vars_new, vars_old):
        print(nfv, ofv)

        assert nfv == ofv


@pytest.mark.parametrize('multivcf_files', [
    [
        'multivcf_split1.vcf',
        'multivcf_split2.vcf'
    ],
    [
        'multivcf_original.vcf'
    ]
])
def test_vcf_loader_multi(fixture_dirname, multivcf_files):
    ped_file = fixture_dirname('backends/multivcf.ped')
    single_vcf = fixture_dirname('backends/multivcf_original.vcf')

    multivcf_files = list(map(
        lambda x: os.path.join(fixture_dirname('backends'), x), multivcf_files
    ))

    families = FamiliesLoader(ped_file).load()
    families_multi = FamiliesLoader(ped_file).load()

    single_loader = VcfLoader(families, [single_vcf])
    assert single_loader is not None
    multi_vcf_loader = VcfLoader(
        families_multi, multivcf_files, fill_missing_ref=False)
    assert multi_vcf_loader is not None
    single_it = single_loader.full_variants_iterator()
    multi_it = multi_vcf_loader.full_variants_iterator()
    for s, m in zip(single_it, multi_it):
        assert s[0] == m[0]
        assert len(s[1]) == 5
        assert len(m[1]) == 5

        s_gt_f1 = s[1][0].genotype
        m_gt_f1 = m[1][0].genotype
        assert all((s_gt_f1 == m_gt_f1).flatten())

        s_gt_f2 = s[1][0].genotype
        m_gt_f2 = m[1][0].genotype
        assert all((s_gt_f2 == m_gt_f2).flatten())

        s_gt_f3 = s[1][0].genotype
        m_gt_f3 = m[1][0].genotype
        assert all((s_gt_f3 == m_gt_f3).flatten())

        s_gt_f4 = s[1][0].genotype
        m_gt_f4 = m[1][0].genotype
        assert all((s_gt_f4 == m_gt_f4).flatten())

        s_gt_f5 = s[1][0].genotype
        m_gt_f5 = m[1][0].genotype
        assert all((s_gt_f5 == m_gt_f5).flatten())


@pytest.mark.parametrize('fill_flag, fill_value', [[True, 0], [False, -1]])
def test_multivcf_loader_fill_missing(fixture_dirname, fill_flag, fill_value):
    ped_file = fixture_dirname('backends/multivcf.ped')

    multivcf_files = [
        fixture_dirname('backends/multivcf_missing1.vcf'),
        fixture_dirname('backends/multivcf_missing2.vcf'),
    ]
    families = FamiliesLoader(ped_file).load()
    params = {
        'vcf_include_reference_genotypes': True,
        'vcf_include_unknown_family_genotypes': True,
        'vcf_include_unknown_person_genotypes': True
    }
    multi_vcf_loader = VcfLoader(families, multivcf_files,
                                 fill_missing_ref=fill_flag,
                                 params=params)
    assert multi_vcf_loader is not None
    multi_it = multi_vcf_loader.full_variants_iterator()
    svs_fvs = [sum_fvs for sum_fvs in multi_it]
    print(svs_fvs)
    first_present = svs_fvs[0]
    second_missing = svs_fvs[1]
    assert next(multi_it, None) is None

    gt1_f1 = first_present[1][0].genotype
    gt1_f1_expected = np.array([
        [1, 1],
        [0, 0],
        [0, 1],
        [0, 1]
    ], dtype=np.int8)
    gt1_f5 = first_present[1][4].genotype
    gt1_f5_expected = np.array([
        [1, 1],
        [0, 0],
        [1, 0],
        [0, 1]
    ], dtype=np.int8)
    assert all((gt1_f1 == gt1_f1_expected).flatten())
    assert all((gt1_f5 == gt1_f5_expected).flatten())
    print(second_missing[1][0], ' ', second_missing[1][0].genotype)
    print(second_missing[1][1], ' ', second_missing[1][1].genotype)

    gt2_f1 = second_missing[1][0].genotype
    gt2_f2 = second_missing[1][1].genotype
    gt2_f3 = second_missing[1][2].genotype
    gt2_f5 = second_missing[1][4].genotype

    gt2_f1_f2_f3_expected = np.array([[fill_value]*2]*4, dtype=np.int8)
    gt2_f5_expected = np.array([
        [0, 0],
        [1, 1],
        [1, 0],
        [0, 1]
    ], dtype=np.int8)

    assert all((gt2_f1 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f2 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f3 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f5 == gt2_f5_expected).flatten())
    assert(svs_fvs[0][0].ref_allele.position == 865582)
    assert(svs_fvs[1][0].ref_allele.position == 865583)
    assert(svs_fvs[2][0].ref_allele.position == 865624)
    assert(svs_fvs[3][0].ref_allele.position == 865627)
    assert(svs_fvs[4][0].ref_allele.position == 865664)
    assert(svs_fvs[5][0].ref_allele.position == 865691)


def test_transform_vcf_genotype():
    genotypes = [
        [0, 0, False],
        [0, 1, False],
        [1, 0, False],
        [1, 1, False],
        [0, True],
        [1, True],
    ]
    expected = np.array([
        [0, 0, 1, 1, 0, 1],
        [0, 1, 0, 1, -2, -2],
        [False, False, False, False, True, True]
    ], dtype=GENOTYPE_TYPE)

    assert np.array_equal(
        expected, VcfLoader.transform_vcf_genotypes(genotypes)
    )
