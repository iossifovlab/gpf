from typing import Any

import sqlglot
from sqlglot import expressions


def to_duckdb_transpile(query: Any) -> Any:
    return sqlglot.transpile(query.sql(), read="duckdb")


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
