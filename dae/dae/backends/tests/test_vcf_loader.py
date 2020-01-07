import pytest


@pytest.mark.parametrize(
    "include_reference_genotypes,"
    "include_unknown_family_genotypes,"
    "include_unknown_person_genotypes,count", [
        (True, True, True, 7),
        (True, True, False, 4),
        (True, False, True, 6),
        (False, True, True, 7),
        (True, False, False, 4),
        (False, False, False, 4),
    ]
)
def test_vcf_loader_params(
    vcf_variants_loader,
    include_reference_genotypes,
    include_unknown_family_genotypes,
    include_unknown_person_genotypes,
    count
):
    params = {
        'include_reference_genotypes': include_reference_genotypes,
        'include_unknown_family_genotypes': include_unknown_family_genotypes,
        'include_unknown_person_genotypes': include_unknown_person_genotypes,
    }

    variants_loader = vcf_variants_loader("backends/f1_test", params=params)
    vs = list(variants_loader.family_variants_iterator())
    assert len(vs) == count
