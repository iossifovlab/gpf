# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import pytest
from dae.pheno.pheno_data import PhenotypeStudy


@pytest.mark.parametrize(
    "filter_type,expected_len", [("apply", 176), ("invert", 19), ("skip", 195)]
)
def test_default_filters(
    fake_phenotype_data: PhenotypeStudy,
    filter_type: str,
    expected_len: int
) -> None:
    measure_id = "i1.m10"
    assert (
        measure_id in fake_phenotype_data.measures
        and fake_phenotype_data.measures[measure_id] is not None
    )
    df = fake_phenotype_data.get_measure_values_df(
        measure_id, default_filter=filter_type
    )
    assert len(df) == expected_len


def test_default_filter_bad_value_throw(
    fake_phenotype_data: PhenotypeStudy
) -> None:
    measure_id = "i1.m10"
    assert (
        measure_id in fake_phenotype_data.measures
        and fake_phenotype_data.measures[measure_id] is not None
    )

    with pytest.raises(ValueError):
        fake_phenotype_data.get_measure_values_df(
            measure_id, default_filter="wrong"
        )
