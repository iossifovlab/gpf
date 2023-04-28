# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.utils.regions import Region
from dae.utils.variant_utils import mat2str


@pytest.mark.parametrize(
    "region,worst_effect,count",
    [
        # (Region('1', 878109, 878109), ("missense", "missense")),
        (Region("1", 901921, 901921), ("synonymous", "missense"), 1),
        (Region("1", 905956, 905956), ("frame-shift", "missense"), 1),
    ],
)
def test_multi_alt_allele_effects(variants_vcf, region, worst_effect, count):
    fvars = variants_vcf("backends/effects_trio_multi")
    vs = list(fvars.query_variants(
        regions=[region], effect_types=["missense"]))

    for v in vs:
        print("------------------")
        print(mat2str(v.best_state))
        print(mat2str(v.gt))
        assert len(v.effects) == 2
        assert v.effects[0].worst == worst_effect[0]
        assert v.effects[1].worst == worst_effect[1]

    assert len(vs) == count
