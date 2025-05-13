# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.query_variants.attribute_queries import (
    transform_attribute_query_to_function,
)
from dae.variants.attributes import Inheritance


@pytest.mark.parametrize(
    "query,exp1,exp2",
    [
        ("denovo", True, False),
        ("not denovo", False, True),
        ("all([denovo, possible_denovo])", False, False),
        ("any([denovo,possible_denovo])", True, True),
        ("denovo or possible_denovo", True, True),
        ("denovo and possible_denovo", False, False),
        ("not denovo and not possible_denovo", False, False),
    ],
)
def test_simple_inheritance_parser(query, exp1, exp2):
    matcher = transform_attribute_query_to_function(Inheritance, query)

    assert matcher(Inheritance.denovo.value) == exp1
    assert matcher(Inheritance.possible_denovo.value) == exp2
