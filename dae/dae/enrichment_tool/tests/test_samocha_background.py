# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Callable

import pytest

from dae.variants.attributes import Inheritance
from dae.studies.study import GenotypeData
from dae.enrichment_tool.event_counters import EventsCounter
from dae.enrichment_tool.genotype_helper import GenotypeHelper
from dae.enrichment_tool.background import SamochaBackground


def test_filename(
        f1_trio_samocha_background: SamochaBackground,
        fixture_dirname: Callable[[str], str]) -> None:
    assert f1_trio_samocha_background.filename == fixture_dirname(
        "studies/f1_trio/enrichment/samochaBackgroundModel.csv"
    )


def test_load(f1_trio_samocha_background: SamochaBackground) -> None:
    f1_trio_samocha_background.load()
    background = f1_trio_samocha_background.background
    assert len(background) == 3

    assert background.iloc[0]["gene"] == "SAMD11"
    assert background.iloc[0]["F"] == 2
    assert background.iloc[0]["M"] == 2
    assert background.iloc[0]["P_LGDS"] == 1.1
    assert background.iloc[0]["P_MISSENSE"] == 1.4
    assert background.iloc[0]["P_SYNONYMOUS"] == 5.7

    assert background.iloc[1]["gene"] == "PLEKHN1"
    assert background.iloc[1]["F"] == 2
    assert background.iloc[1]["M"] == 2
    assert background.iloc[1]["P_LGDS"] == 1.2
    assert background.iloc[1]["P_MISSENSE"] == 1.5
    assert background.iloc[1]["P_SYNONYMOUS"] == 5.8

    assert background.iloc[2]["gene"] == "POGZ"
    assert background.iloc[2]["F"] == 2
    assert background.iloc[2]["M"] == 2
    assert background.iloc[2]["P_LGDS"] == 6.3
    assert background.iloc[2]["P_MISSENSE"] == 4.6
    assert background.iloc[2]["P_SYNONYMOUS"] == 2.9


def test_calc_stats(
    f1_trio: GenotypeData, f1_trio_samocha_background: SamochaBackground
) -> None:
    # pylint: disable=too-many-statements
    variants = list(
        f1_trio.query_variants(inheritance=str(Inheritance.denovo.name))
    )
    event_counter = EventsCounter()

    psc = f1_trio.get_person_set_collection("phenotype")
    helper = GenotypeHelper(f1_trio, psc)
    children_by_sex = helper.children_by_sex("phenotype1")

    enrichment_events = event_counter.events(
        variants, children_by_sex, set(["missense", "synonymous"])
    )

    assert enrichment_events["all"].events is not None
    assert len(enrichment_events["all"].events) == 2
    assert enrichment_events["all"].events == [["SAMD11"], ["SAMD11"]]
    assert enrichment_events["all"].expected is None
    assert enrichment_events["all"].pvalue is None

    assert enrichment_events["rec"].events is not None
    assert len(enrichment_events["rec"].events) == 1
    assert enrichment_events["rec"].events == [["SAMD11"]]
    assert enrichment_events["rec"].expected is None
    assert enrichment_events["rec"].pvalue is None

    assert enrichment_events["male"].events is not None
    assert len(enrichment_events["male"].events) == 1
    assert enrichment_events["male"].events == [["SAMD11"]]
    assert enrichment_events["male"].expected is None
    assert enrichment_events["male"].pvalue is None

    assert enrichment_events["female"].events is not None
    assert len(enrichment_events["female"].events) == 1
    assert enrichment_events["female"].events == [["SAMD11"]]
    assert enrichment_events["female"].expected is None
    assert enrichment_events["female"].pvalue is None

    assert enrichment_events["unspecified"].events is not None
    assert len(enrichment_events["unspecified"].events) == 0
    assert enrichment_events["unspecified"].events == []
    assert enrichment_events["unspecified"].expected is None
    assert enrichment_events["unspecified"].pvalue is None

    result = f1_trio_samocha_background.calc_stats(
        ["missense"],
        enrichment_events,
        ["SAMD11", "PLEKHN1", "POGZ"],
        children_by_sex,
    )

    assert result == enrichment_events

    assert result["all"].events is not None
    assert len(result["all"].events) == 2
    assert result["all"].events == [["SAMD11"], ["SAMD11"]]
    assert result["all"].expected == 30.0
    assert result["all"].pvalue == pytest.approx(9.002e-11)

    assert result["rec"].events is not None
    assert len(result["rec"].events) == 1
    assert result["rec"].events == [["SAMD11"]]
    assert result["rec"].expected == 15.0
    assert result["rec"].pvalue == pytest.approx(9.788e-6, rel=1e-3)

    assert result["male"].events is not None
    assert len(result["male"].events) == 1
    assert result["male"].events == [["SAMD11"]]
    assert result["male"].expected == 15.0
    assert result["male"].pvalue == pytest.approx(9.788e-06, rel=1e-3)

    assert result["female"].events is not None
    assert len(result["female"].events) == 1
    assert result["female"].events == [["SAMD11"]]
    assert result["female"].expected == 15.0
    assert result["female"].pvalue == pytest.approx(9.788e-06, rel=1e-3)

    assert result["unspecified"].events is not None
    assert len(result["unspecified"].events) == 0
    assert result["unspecified"].events == []
    assert result["unspecified"].expected is None
    assert result["unspecified"].pvalue is None
