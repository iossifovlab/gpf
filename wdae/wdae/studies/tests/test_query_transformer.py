# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from studies.query_transformer import QueryTransformer


@pytest.mark.parametrize(
    "affected_status,expected_query",
    [
        (
            ["affected only"],
            "(affected and not unaffected)",
        ),
        (
            ["unaffected only"],
            "(unaffected and not affected)",
        ),
        (
            ["affected and unaffected"],
            "(affected and unaffected)",
        ),
        (
            ["affected only", "unaffected only"],
            "(affected and not unaffected) or (unaffected and not affected)",
        ),
        (
            ["affected only", "affected and unaffected"],
            "(affected and not unaffected) or (affected and unaffected)",
        ),
        (
            ["unaffected only", "affected and unaffected"],
            "(unaffected and not affected) or (affected and unaffected)",
        ),
        (
            ["affected only", "unaffected only", "affected and unaffected"],
            "(affected and not unaffected) or (unaffected and not affected)"
            " or (affected and unaffected)",
        ),
    ],
)
def test_affected_status(
    affected_status: list[str],
    expected_query: str,
) -> None:
    parents_query = QueryTransformer._affected_status_to_query(affected_status)

    assert parents_query == expected_query
