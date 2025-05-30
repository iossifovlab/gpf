# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.person_sets import (
    PersonSetCollection,
    PSCQuery,
)
from dae.person_sets.person_sets import (
    AttributeQueriesUnsupportedException,
)


@pytest.mark.parametrize("query, expected", [
    (PSCQuery("phenotype", {"autism"}),
     {"affected_statuses": "any([affected])"}),
    (PSCQuery("phenotype", {"unaffected"}),
     {"affected_statuses": "any([unaffected])"}),
    (PSCQuery("phenotype", {"unspecified"}),
     {"affected_statuses": "any([unspecified])"}),
    (PSCQuery("phenotype", {"autism", "unaffected"}),
     {"affected_statuses": "any([affected,unaffected])"}),
    (PSCQuery("phenotype", {"autism", "unaffected", "unspecified"}),
     {"affected_statuses": "any([affected,unaffected,unspecified])"}),
])
def test_phenotype_psc_query_transform_phenotype(
    phenotype_psc: PersonSetCollection,
    query: PSCQuery,
    expected: dict[str, str] | None,
) -> None:
    assert phenotype_psc is not None
    result = phenotype_psc.transform_ps_query_to_attribute_queries(query)

    assert result == expected


def test_phenotype_transform_errors_on_ps_not_found(
    phenotype_psc: PersonSetCollection,
) -> None:
    query = PSCQuery("phenotype", {"developmental_disorder"})
    with pytest.raises(ValueError, match=r"Selected person sets.+"):
        phenotype_psc.transform_ps_query_to_attribute_queries(query)


def test_default_person_set_is_not_supported(
    phenotype_psc: PersonSetCollection,
) -> None:
    query = PSCQuery("phenotype", {"unknown"})
    with pytest.raises(AttributeQueriesUnsupportedException):
        phenotype_psc.transform_ps_query_to_attribute_queries(query)


@pytest.mark.parametrize("query, expected", [
    (PSCQuery("status", {"affected"}),
     {"affected_statuses": "any([affected])"}),
    (PSCQuery("status", {"unaffected"}),
     {"affected_statuses": "any([unaffected])"}),
    (PSCQuery("status", {"unspecified"}),
     {"affected_statuses": "any([unspecified])"}),
    (PSCQuery("status", {"affected", "unaffected"}),
     {"affected_statuses": "any([affected,unaffected])"}),
])
def test_status_psc_query_transform_phenotype(
    status_psc: PersonSetCollection,
    query: PSCQuery,
    expected: dict[str, str] | None,
) -> None:
    assert status_psc is not None
    result = status_psc.transform_ps_query_to_attribute_queries(query)

    assert result == expected


@pytest.mark.parametrize("query, expected", [
    (PSCQuery("status_sex", {"affected_male"}),
     {"affected_statuses": "any([affected])", "sexes": "any([M])"}),
    (PSCQuery("status_sex", {"affected_male", "affected_female"}),
     {"affected_statuses": "any([affected])", "sexes": "any([F,M])"}),
    (PSCQuery("status_sex", {"affected_male", "unaffected_male"}),
     {"affected_statuses": "any([affected,unaffected])", "sexes": "any([M])"}),
])
def test_status_sex_psc_query_transform_phenotype(
    status_sex_psc: PersonSetCollection,
    query: PSCQuery,
    expected: dict[str, str] | None,
) -> None:
    assert status_sex_psc is not None
    result = status_sex_psc.transform_ps_query_to_attribute_queries(query)

    assert result == expected


def test_multi_source_multi_value_not_supported(
    status_sex_psc: PersonSetCollection,
) -> None:
    query = PSCQuery("status_sex", {"affected_male", "unaffected_female"})
    with pytest.raises(AttributeQueriesUnsupportedException):
        status_sex_psc.transform_ps_query_to_attribute_queries(query)
