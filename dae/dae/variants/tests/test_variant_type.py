import pytest

from dae.variants.core import Allele


@pytest.mark.parametrize(
    "allele_type",
    [
        Allele.Type.small_insertion,
        Allele.Type.small_deletion,
        Allele.Type.tandem_repeat_del,
        Allele.Type.tandem_repeat_ins,
    ])
def test_is_indel(allele_type):
    assert allele_type & Allele.Type.indel
