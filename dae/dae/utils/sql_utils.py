from typing import Any

import sqlglot
from sqlglot import expressions


def to_duckdb_transpile(query: Any) -> str:
    return sqlglot.transpile(query.sql(), read="duckdb")[0]

def glot_and(left_expr: Any, right_expr: Any) -> Any:
    return left_expr.and_(right_expr)


def fill_query_parameters(query: Any, params: list[Any]) -> None:
    """Filll query parameters."""
    placeholders = list(query.find_all(expressions.Placeholder))
    if len(placeholders) != len(params):
        raise ValueError(
            f"Query has {len(params)} parameters,"
            f" received: {len(placeholders)}",
        )
    for placeholder, param in zip(placeholders, params, strict=True):
        placeholder.replace(param)
