# pylint: disable=W0621,C0114,C0116,W0212,W0613
from sqlglot import parse_one


def test_summary_query_builder() -> None:
    sql = """
WITH summary AS (
SELECT *
  FROM
    summary_table AS sa
  WHERE
    ( sa.region_bin IN ('chr14_0')) AND
    ( ( sa.chromosome = 'chr14' AND
      ((sa.position >= 21365194 AND sa.position <= 21457298) OR
       (COALESCE(sa.end_position, -1) >= 21365194 AND
        COALESCE(sa.end_position, -1) <= 21457298) OR
       (21365194 >= sa.position AND
        21457298 <= COALESCE(sa.end_position, -1)))
    ) ) AND
    ( sa.allele_index > 0 )
)
SELECT count(*)
FROM summary
CROSS JOIN
    (SELECT UNNEST (summary.effect_gene) as eg)
WHERE
    eg.effect_gene_symbols in ('CHD8');
    """
    expr = parse_one(sql)
    assert expr
