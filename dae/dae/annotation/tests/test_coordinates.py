# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.utils.dae_utils import dae2vcf_variant
from dae.variants.variant import SummaryAllele


@pytest.mark.parametrize(
    "variant,check_pos,check_cshl_pos,check_ref,check_alt",
    [
        ("sub(A->T)", 150013938, 150013938, "A", "T"),
        ("ins(AA)", 150013937, 150013937, "A", "AAA"),
        ("del(1)", 150013937, 150013937, "AA", "A"),
        ("comp(AA->G)", 150013938, 150013938, "AA", "G"),
    ],
)
def test_dae2vcf(
    mocker, variant, check_pos, check_cshl_pos, check_ref, check_alt
):

    genome = mocker.Mock()
    genome.get_sequence = lambda _, start, end: "A" * (end - start + 1)

    pos, ref, alt = dae2vcf_variant("chr1", 150013938, variant, genome)

    assert pos == check_pos
    assert ref == check_ref
    assert alt == check_alt

    summary = SummaryAllele("chr1", pos, ref, alt)
    assert summary is not None

    assert summary.cshl_position == check_cshl_pos
    assert summary.cshl_location == f"chr1:{check_cshl_pos}"
    assert summary.cshl_variant == variant
