import pytest

from dae.variants.attributes import VariantType


@pytest.mark.parametrize(
    "variant_type",
    [
        VariantType.insertion,
        VariantType.deletion,
        VariantType.tandem_repeat_del,
        VariantType.tandem_repeat_ins,
    ])
def test_is_indel(variant_type):
    assert variant_type & VariantType.indel
