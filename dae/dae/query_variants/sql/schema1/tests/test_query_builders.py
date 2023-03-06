import pytest
from dae.query_variants.sql.schema1.base_query_builder import BaseQueryBuilder
from dae.utils.regions import Region


@pytest.fixture()
def query_builder():
    return BaseQueryBuilder


def test_regions(query_builder):
    query = query_builder._build_regions_where(
        query_builder, [Region("X", 5, 15)]
    )
    assert ("(`chromosome` = 'X' AND ((`position` >= 5 AND `position` <= 15)"
            + " OR (COALESCE(end_position, -1) >= 5"
            + " AND COALESCE(end_position, -1) <= 15)"
            + " OR (5 >= `position` AND 15 <= COALESCE(end_position, -1))))"
            ) in query

    query = query_builder._build_regions_where(query_builder, [
        Region('13')
    ])
    assert "(`chromosome` = '13')" in query
