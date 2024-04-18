# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.utils.regions import Region
from impala_storage.schema1.base_query_builder import BaseQueryBuilder


def test_regions() -> None:
    query = BaseQueryBuilder._build_regions_where(
        [Region("X", 5, 15)],
    )
    assert ("(`chromosome` = 'X' AND ((`position` >= 5 AND `position` <= 15)"
            + " OR (COALESCE(end_position, -1) >= 5"
            + " AND COALESCE(end_position, -1) <= 15)"
            + " OR (5 >= `position` AND 15 <= COALESCE(end_position, -1))))"
            ) in query

    query = BaseQueryBuilder._build_regions_where([
        Region("13"),
    ])
    assert "(`chromosome` = '13')" in query
