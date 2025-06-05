# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.person_sets import (
    PersonSetCollection,
    PSCQuery,
)


@pytest.mark.parametrize("query, count", [
    (PSCQuery("phenotype", {"autism"}), 5),
    (PSCQuery("phenotype", {"developmental_disorder"}), 0),
    (PSCQuery("phenotype", {"unaffected"}), 4),
    (PSCQuery("phenotype", {"unspecified"}), 2),
    (PSCQuery("phenotype", {"autism", "unaffected"}), 9),
    (PSCQuery("phenotype", {"autism", "unaffected", "unspecified"}), None),
])
def test_phenotype_psc_query(
    phenotype_psc: PersonSetCollection,
    query: PSCQuery,
    count: int | None,
) -> None:
    assert phenotype_psc is not None
    result = phenotype_psc.query_person_ids(query)

    if count is None:
        assert result is None
    else:
        assert result is not None
        assert len(result) == count


@pytest.mark.parametrize("query, count", [
    (PSCQuery("status", {"affected", "unaffected", "unknown"}), 9),
    (PSCQuery("status", {"affected"}), 5),
])
def test_status_psc_query(
    status_psc: PersonSetCollection,
    query: PSCQuery,
    count: int | None,
) -> None:
    assert status_psc is not None
    result = status_psc.query_person_ids(query)

    if count is None:
        assert result is None
    else:
        assert result is not None
        assert len(result) == count


@pytest.mark.parametrize("query, count", [
    (PSCQuery(
        "status_sex",
        {
            "affected_male", "affected_female",
            "unaffected_male", "unaffected_female",
            "unknown"}), None),
    (PSCQuery("status_sex", {"affected_male"}), 2),
    (PSCQuery("status_sex", {"affected_female"}), 3),
])
def test_status_sex_psc_query(
    status_sex_psc: PersonSetCollection,
    query: PSCQuery,
    count: int | None,
) -> None:
    assert status_sex_psc is not None
    result = status_sex_psc.query_person_ids(query)

    if count is None:
        assert result is None
    else:
        assert result is not None
        assert len(result) == count
