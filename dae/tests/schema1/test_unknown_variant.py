# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.utils.regions import Region
from dae.utils.variant_utils import mat2str


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "region,count,members",
    [
        (Region("1", 11500, 11500), 1, ["mom1", None, None]),
        (Region("1", 11501, 11501), 1, ["mom1", None, "ch1"]),
        (Region("1", 11502, 11502), 1, [None, None, "ch1"]),
        (Region("1", 11503, 11503), 1, ["mom1", "dad1", "ch1"]),
    ],
)
def test_variant_in_members(variants_impl, variants, region, count, members):
    fvars = variants_impl(variants)("backends/unknown_trio")
    vs = list(fvars.query_variants(regions=[region]))
    assert len(vs) == count
    for v in vs:
        print(v, mat2str(v.best_state))
        for aa in v.alt_alleles:
            print(aa, aa.variant_in_members)
            assert list(aa.variant_in_members) == members
