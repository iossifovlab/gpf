# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import subprocess
import sys

import pytest

from gpf.enrichment_tool.event_counters import (
    EventsCounter,
    filter_denovo_one_event_per_family,
    filter_denovo_one_gene_per_events,
    filter_denovo_one_gene_per_recurrent_events,
    get_sym_2_fn,
)
from gpf.enrichment_tool.genotype_helper import (
    AlleleEvent,
    GeneEffect,
    VariantEvent,
)
from gpf.person_sets import ChildrenBySex


@pytest.mark.parametrize(
    "variant_events,expected", [
        (  # one event in one family
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
            ],
            [["G1"]],
        ),
        (  # two events in two families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        {("f2", "child2")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
            ],
            [["G1"], ["G1"]],
        ),
        (  # two events in one family
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f1", "chr1:2:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
            ],
            [["G1"]],
        ),
        (  # two events in two families; the second event effect is not in
           # the requested effect types
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        {("f2", "child2")},
                        {GeneEffect("G1", "intronic")},
                    ),
                ]),
            ],
            [["G1"]],
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        {("f2", "child2")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        {("f3", "child3")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
            ],
            [["G1"], ["G1"], ["G1"]],
        ),
    ],
)
def test_filter_denovo_one_event_per_family(
    variant_events: list[VariantEvent],
    expected: list[list[str]],
) -> None:
    res = filter_denovo_one_event_per_family(
        variant_events, {"missense", "synonymous"},
    )

    assert res == expected


@pytest.mark.parametrize(
    "variant_events,expected", [
        (  # one event in one family
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
            ],
            [],
        ),
        (  # two events in two families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        {("f2", "child2")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
            ],
            [["G1"]],
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        {("f2", "child2")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        {("f3", "child3")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
            ],
            [["G1"]],
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        {("f2", "child2")},
                        {
                            GeneEffect("G1", "missense"),
                            GeneEffect("G2", "synonymous"),
                        },
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        {("f3", "child3")},
                        {GeneEffect("G2", "missense")},
                    ),
                ]),
            ],
            [["G1"], ["G2"]],
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        {("f2", "child2")},
                        {
                            GeneEffect("G1", "missense"),
                            GeneEffect("G2", "synonymous"),
                        },
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        {("f3", "child3")},
                        {GeneEffect("G2", "intergenic")},
                    ),
                ]),
            ],
            [["G1"]],
        ),
    ],
)
def test_filter_denovo_one_gene_per_recurrent_events(
    variant_events: list[VariantEvent],
    expected: list[list[str]],
) -> None:
    res = filter_denovo_one_gene_per_recurrent_events(
        variant_events, {"missense", "synonymous"},
    )

    assert res == expected


@pytest.mark.parametrize(
    "variant_events,expected", [
        (  # one event in one family
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
            ],
            [["G1"]],
        ),
        (  # two events in two families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        {("f2", "child2")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
            ],
            [["G1"]],
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        {("f2", "child2")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        {("f3", "child3")},
                        {GeneEffect("G2", "missense")},
                    ),
                ]),
            ],
            [["G1"], ["G2"]],
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        {("f2", "child2")},
                        {
                            GeneEffect("G1", "missense"),
                            GeneEffect("G2", "synonymous"),
                        },
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        {("f3", "child3")},
                        {GeneEffect("G2", "missense")},
                    ),
                ]),
            ],
            [["G1"], ["G2"]],
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        {("f2", "child2")},
                        {
                            GeneEffect("G1", "missense"),
                            GeneEffect("G2", "synonymous"),
                        },
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        {("f3", "child3")},
                        {GeneEffect("G2", "intergenic")},
                    ),
                ]),
            ],
            [["G1"], ["G2"]],
        ),
    ],
)
def test_filter_denovo_one_gene_per_events(
    variant_events: list[VariantEvent],
    expected: list[list[str]],
) -> None:
    res = filter_denovo_one_gene_per_events(
        variant_events, {"missense", "synonymous"},
    )

    assert res == expected


@pytest.mark.parametrize(
    "variant_events,expected", [
        (  # one event in one family
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
            ],
            {"G1": 1},
        ),
        (  # two events in two families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        {("f2", "child2")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
            ],
            {"G1": 2},
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        {("f2", "child2")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        {("f3", "child3")},
                        {GeneEffect("G2", "missense")},
                    ),
                ]),
            ],
            {"G1": 2, "G2": 1},
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        {("f2", "child2")},
                        {
                            GeneEffect("G1", "missense"),
                            GeneEffect("G2", "synonymous"),
                        },
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        {("f3", "child3")},
                        {GeneEffect("G2", "missense")},
                    ),
                ]),
            ],
            {"G1": 2, "G2": 2},
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        {("f1", "child1")},
                        {GeneEffect("G1", "missense")},
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        {("f2", "child2")},
                        {
                            GeneEffect("G1", "missense"),
                            GeneEffect("G2", "synonymous"),
                        },
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        {("f3", "child3")},
                        {GeneEffect("G2", "intergenic")},
                    ),
                ]),
            ],
            {"G1": 2, "G2": 1},
        ),
    ],
)
def test_get_sym_2_fn(
    variant_events: list[VariantEvent],
    expected: dict[str, int],
) -> None:
    res = get_sym_2_fn(
        variant_events, {"missense", "synonymous"},
    )

    assert res == expected


def _v1_f1() -> VariantEvent:
    return VariantEvent("f1", "chr1:1:A:C:f1", [
        AlleleEvent(
            {("f1", "child1")},
            {GeneEffect("A", "missense")},
        ),
    ])


def _v2_f1() -> VariantEvent:
    return VariantEvent("f1", "chr1:2:A:C:f1", [
        AlleleEvent(
            {("f1", "child1")},
            {GeneEffect("A", "missense"), GeneEffect("B", "missense")},
        ),
    ])


@pytest.mark.parametrize(
    "variant_events", [
        pytest.param([_v1_f1(), _v2_f1()], id="v1_then_v2"),
        pytest.param([_v2_f1(), _v1_f1()], id="v2_then_v1"),
    ],
)
def test_filter_denovo_one_event_per_family_ignores_input_order(
    variant_events: list[VariantEvent],
) -> None:
    res = filter_denovo_one_event_per_family(variant_events, {"missense"})

    assert res == [["A"], ["B"]]


@pytest.mark.parametrize("hash_seed", ["0", "1", "2", "3"])
def test_filter_denovo_one_event_per_family_sorts_genes_of_an_event(
    hash_seed: str,
) -> None:
    # The genes of an event come from a set of strings, and the order of a
    # set of strings depends on the hash seed of the process.
    code = (
        "from gpf.enrichment_tool.event_counters import "
        "filter_denovo_one_event_per_family\n"
        "from gpf.enrichment_tool.genotype_helper import "
        "AlleleEvent, GeneEffect, VariantEvent\n"
        "ve = VariantEvent('f1', 'chr1:1:A:C:f1', [AlleleEvent("
        "{('f1', 'child1')}, "
        "{GeneEffect('B', 'missense'), GeneEffect('A', 'missense')})])\n"
        "print(filter_denovo_one_event_per_family([ve], {'missense'}))\n"
    )

    out = subprocess.run(
        [sys.executable, "-c", code],
        env={**os.environ, "PYTHONHASHSEED": hash_seed},
        capture_output=True, text=True, check=True,
    )

    assert out.stdout.strip() == "[['A', 'B']]"


def test_events_counter_ignores_input_order() -> None:
    children_by_sex = ChildrenBySex(
        male={("f1", "child1")},
        female={("f2", "child2")},
        unspecified={("f3", "child3")},
    )
    variant_events = [
        _v1_f1(),
        _v2_f1(),
        VariantEvent("f2", "chr1:3:A:C:f2", [
            AlleleEvent(
                {("f2", "child2")},
                {GeneEffect("A", "missense"), GeneEffect("C", "missense")},
            ),
        ]),
        VariantEvent("f3", "chr1:4:A:C:f3", [
            AlleleEvent(
                {("f3", "child3")},
                {GeneEffect("A", "missense")},
            ),
        ]),
    ]
    counter = EventsCounter()

    forward = counter.events(variant_events, children_by_sex, {"missense"})
    backward = counter.events(
        list(reversed(variant_events)), children_by_sex, {"missense"})

    assert forward == backward
