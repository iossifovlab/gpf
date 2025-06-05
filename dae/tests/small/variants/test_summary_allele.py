# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import pytest

from dae.variants.variant import SummaryAllele


@pytest.mark.parametrize(
    "sa,end_position",
    [
        (SummaryAllele("1", 11539, "T", "A", summary_index=0, allele_index=0),
         11539),
        (SummaryAllele("1", 11539, "T", "TA", summary_index=0, allele_index=1),
         11539),
        (SummaryAllele("1", 11539, "TG", "T", summary_index=0, allele_index=2),
         11540),
    ],
)
def test_summary_allele_end_position(
    sa: SummaryAllele, end_position: int,
) -> None:
    assert sa.end_position == end_position
