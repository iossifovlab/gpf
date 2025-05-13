# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.person_sets import (
    PersonSetCollection,
    PSCQuery,
)


@pytest.mark.parametrize("query, expected", [
    (PSCQuery("phenotype", {"autism"}),
     {"affected_statuses": "any([affected])"}),
    (PSCQuery("phenotype", {"developmental_disorder"}),
     {}),
    (PSCQuery("phenotype", {"unaffected"}),
     {"affected_statuses": "any([unaffected])"}),
    (PSCQuery("phenotype", {"unspecified"}),
     {"affected_statuses": "any([unspecified])"}),
    (PSCQuery("phenotype", {"autism", "unaffected"}),
     {"affected_statuses": "any([affected,unaffected])"}),
    (PSCQuery("phenotype", {"autism", "unaffected", "unspecified"}),
     {"affected_statuses": "any([affected,unaffected,unspecified])"}),
    (PSCQuery("phenotype", {"unknown"}),
     {"affected_statuses":
      "((not affected) and (not unaffected) and (not unspecified))"}),
])
def test_phenotype_psc_query_transform_phenotype(
    phenotype_psc: PersonSetCollection,
    query: PSCQuery,
    expected: dict[str, str] | None,
) -> None:
    assert phenotype_psc is not None
    result = phenotype_psc.transform_pedigree_queries(query)

    assert result == expected


@pytest.mark.parametrize("query, expected", [
    (PSCQuery("status", {"affected"}),
     {"affected_statuses": "any([affected])"}),
    (PSCQuery("status", {"unaffected"}),
     {"affected_statuses": "any([unaffected])"}),
    (PSCQuery("status", {"unspecified"}),
     {"affected_statuses": "any([unspecified])"}),
    (PSCQuery("status", {"affected", "unaffected"}),
     {"affected_statuses": "any([affected,unaffected])"}),
    (PSCQuery("status", {"affected", "unaffected", "unspecified"}),
     {"affected_statuses": "any([affected,unaffected,unspecified])"}),
    (PSCQuery("status", {"unknown"}),
     {"affected_statuses":
      "((not affected) and (not unaffected) and (not unspecified))"}),
])
def test_status_psc_query_transform_phenotype(
    status_psc: PersonSetCollection,
    query: PSCQuery,
    expected: dict[str, str] | None,
) -> None:
    assert status_psc is not None
    result = status_psc.transform_pedigree_queries(query)

    assert result == expected


@pytest.mark.parametrize("query, expected", [
    (PSCQuery("status_sex", {"affected_male"}),
     {"affected_statuses": "any([affected])", "sexes": "any([M])"}),
    (PSCQuery("status_sex", {"affected_male", "affected_female"}),
     {"affected_statuses": "any([affected])", "sexes": "any([F,M])"}),
    (PSCQuery("status_sex", {"affected_male", "unaffected_male"}),
     {"affected_statuses": "any([affected,unaffected])", "sexes": "any([M])"}),
    (PSCQuery("status_sex", {"affected_male", "unaffected_female"}),
     None),
    (PSCQuery("status_sex", {"unknown"}),
     None),
])
def test_status_sex_psc_query_transform_phenotype(
    status_sex_psc: PersonSetCollection,
    query: PSCQuery,
    expected: dict[str, str] | None,
) -> None:
    assert status_sex_psc is not None
    result = status_sex_psc.transform_pedigree_queries(query)

    assert result == expected
