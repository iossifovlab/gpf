# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.enrichment_tool.event_counters import (
    filter_denovo_one_event_per_family,
    filter_denovo_one_gene_per_events,
    filter_denovo_one_gene_per_recurrent_events,
    get_sym_2_fn,
)
from dae.enrichment_tool.genotype_helper import (
    AlleleEvent,
    GeneEffect,
    VariantEvent,
)


@pytest.mark.parametrize(
    "variant_events,expected", [
        (  # one event in one family
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
            ],
            [["G1"]],
        ),
        (  # two events in two families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        set([("f2", "child2")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
            ],
            [["G1"], ["G1"]],
        ),
        (  # two events in one family
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f1", "chr1:2:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
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
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        set([("f2", "child2")]),
                        set([GeneEffect("G1", "intronic")]),
                    ),
                ]),
            ],
            [["G1"]],
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        set([("f2", "child2")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        set([("f3", "child3")]),
                        set([GeneEffect("G1", "missense")]),
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
        variant_events, set(["missense", "synonymous"]),
    )

    assert res == expected


@pytest.mark.parametrize(
    "variant_events,expected", [
        (  # one event in one family
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
            ],
            [],
        ),
        (  # two events in two families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        set([("f2", "child2")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
            ],
            [["G1"]],
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        set([("f2", "child2")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        set([("f3", "child3")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
            ],
            [["G1"]],
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        set([("f2", "child2")]),
                        set([
                            GeneEffect("G1", "missense"),
                            GeneEffect("G2", "synonymous"),
                        ]),
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        set([("f3", "child3")]),
                        set([GeneEffect("G2", "missense")]),
                    ),
                ]),
            ],
            [["G1"], ["G2"]],
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        set([("f2", "child2")]),
                        set([
                            GeneEffect("G1", "missense"),
                            GeneEffect("G2", "synonymous"),
                        ]),
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        set([("f3", "child3")]),
                        set([GeneEffect("G2", "intergenic")]),
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
        variant_events, set(["missense", "synonymous"]),
    )

    assert res == expected


@pytest.mark.parametrize(
    "variant_events,expected", [
        (  # one event in one family
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
            ],
            [["G1"]],
        ),
        (  # two events in two families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        set([("f2", "child2")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
            ],
            [["G1"]],
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        set([("f2", "child2")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        set([("f3", "child3")]),
                        set([GeneEffect("G2", "missense")]),
                    ),
                ]),
            ],
            [["G1"], ["G2"]],
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        set([("f2", "child2")]),
                        set([
                            GeneEffect("G1", "missense"),
                            GeneEffect("G2", "synonymous"),
                        ]),
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        set([("f3", "child3")]),
                        set([GeneEffect("G2", "missense")]),
                    ),
                ]),
            ],
            [["G1"], ["G2"]],
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        set([("f2", "child2")]),
                        set([
                            GeneEffect("G1", "missense"),
                            GeneEffect("G2", "synonymous"),
                        ]),
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        set([("f3", "child3")]),
                        set([GeneEffect("G2", "intergenic")]),
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
        variant_events, set(["missense", "synonymous"]),
    )

    assert res == expected


@pytest.mark.parametrize(
    "variant_events,expected", [
        (  # one event in one family
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
            ],
            {"G1": 1},
        ),
        (  # two events in two families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        set([("f2", "child2")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
            ],
            {"G1": 2},
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        set([("f2", "child2")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        set([("f3", "child3")]),
                        set([GeneEffect("G2", "missense")]),
                    ),
                ]),
            ],
            {"G1": 2, "G2": 1},
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        set([("f2", "child2")]),
                        set([
                            GeneEffect("G1", "missense"),
                            GeneEffect("G2", "synonymous"),
                        ]),
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        set([("f3", "child3")]),
                        set([GeneEffect("G2", "missense")]),
                    ),
                ]),
            ],
            {"G1": 2, "G2": 2},
        ),
        (  # three events in three families
            [
                VariantEvent("f1", "chr1:1:A:C:f1", [
                    AlleleEvent(
                        set([("f1", "child1")]),
                        set([GeneEffect("G1", "missense")]),
                    ),
                ]),
                VariantEvent("f2", "chr1:2:A:C:f2", [
                    AlleleEvent(
                        set([("f2", "child2")]),
                        set([
                            GeneEffect("G1", "missense"),
                            GeneEffect("G2", "synonymous"),
                        ]),
                    ),
                ]),
                VariantEvent("f3", "chr1:3:A:C:f3", [
                    AlleleEvent(
                        set([("f3", "child3")]),
                        set([GeneEffect("G2", "intergenic")]),
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
        variant_events, set(["missense", "synonymous"]),
    )

    assert res == expected
