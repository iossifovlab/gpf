# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.utils.regions import Region
from dae.utils.variant_utils import mat2str


def test_trios_multi_single_allele1_full(variants_vcf):
    fvars = variants_vcf("backends/trios_multi")
    variants = list(
        fvars.query_variants(
            regions=[Region("1", 11500, 11500)],
            return_reference=True,
            return_unknown=True,
        )
    )
    assert len(variants) == 1
    for v in variants:
        print(mat2str(v.best_state))
        assert v.best_state.shape == (3, 3)


def test_trios_multi_single_allele2_full(variants_vcf):
    fvars = variants_vcf("backends/trios_multi")
    variants = list(
        fvars.query_variants(
            regions=[Region("1", 11501, 11501)],
            return_reference=True,
            return_unknown=True,
        )
    )
    assert len(variants) == 1
    for v in variants:
        assert v.best_state.shape == (3, 3)


def test_trios_multi_all_reference_full(variants_vcf):
    fvars = variants_vcf("backends/trios_multi")
    variants = list(
        fvars.query_variants(
            regions=[Region("1", 11502, 11502)],
            return_reference=True,
            return_unknown=True,
        )
    )
    assert len(variants) == 1
    for v in variants:
        print(mat2str(v.best_state))
        assert v.best_state.shape == (3, 3)


def test_trios_multi_unknown_full(variants_vcf):
    fvars = variants_vcf("backends/trios_multi")
    variants = list(
        fvars.query_variants(
            regions=[Region("1", 11503, 11503)],
            return_reference=True,
            return_unknown=True,
        )
    )
    assert len(variants) == 1
    for v in variants:
        print(mat2str(v.best_state))
        assert v.best_state.shape == (3, 3)


def test_trios_multi_multi_full(variants_vcf):
    fvars = variants_vcf("backends/trios_multi")
    variants = list(
        fvars.query_variants(
            regions=[Region("1", 11504, 11504)],
            return_reference=True,
            return_unknown=True,
        )
    )
    assert len(variants) == 1
    for v in variants:
        print(mat2str(v.best_state))
        assert v.best_state.shape == (3, 3)


def test_trios_multi_multi3_full(variants_vcf):
    fvars = variants_vcf("backends/trios_multi")
    variants = list(
        fvars.query_variants(
            regions=[Region("1", 11505, 11505)],
            return_reference=True,
            return_unknown=True,
        )
    )
    assert len(variants) == 1
    for v in variants:
        print(mat2str(v.best_state))
        assert v.best_state.shape == (4, 3)

    fvars = variants_vcf("backends/trios_multi")
    variants = list(
        fvars.query_variants(
            regions=[Region("1", 11506, 11506)],
            return_reference=True,
            return_unknown=True,
        )
    )
    assert len(variants) == 1
    for v in variants:
        print(mat2str(v.best_state))
        assert v.best_state.shape == (4, 3)
