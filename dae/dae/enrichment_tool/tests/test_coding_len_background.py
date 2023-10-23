# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Callable

from dae.variants.attributes import Inheritance
from dae.studies.study import GenotypeData

from dae.enrichment_tool.background import CodingLenBackground
from dae.enrichment_tool.event_counters import EventsCounter
from dae.enrichment_tool.genotype_helper import GenotypeHelper


def test_filename(
        f1_trio_coding_len_background: CodingLenBackground,
        fixture_dirname: Callable[[str], str]) -> None:
    assert f1_trio_coding_len_background.filename == fixture_dirname(
        "studies/f1_trio/enrichment/codingLenBackgroundModel.csv"
    )


def test_load(f1_trio_coding_len_background: CodingLenBackground) -> None:
    f1_trio_coding_len_background.load()
    background = f1_trio_coding_len_background.background

    assert len(background) == 3
    assert background.iloc[0]["sym"] == "SAMD11"
    assert background.iloc[0]["raw"] == 3
    assert background.iloc[1]["sym"] == "PLEKHN1"
    assert background.iloc[1]["raw"] == 7
    assert background.iloc[2]["sym"] == "POGZ"
    assert background.iloc[2]["raw"] == 13


def test_calc_stats(
        f1_trio: GenotypeData,
        f1_trio_coding_len_background: CodingLenBackground) -> None:
    # pylint: disable=too-many-statements
    variants = list(
        f1_trio.query_variants(inheritance=str(Inheritance.denovo.name))
    )

    for fv in variants:
        print(80 * "-")
        print(fv, fv.effects)
        for fa in fv.alleles:
            print("\t", fa, fa.effects)

    event_counter = EventsCounter()

    psc = f1_trio.get_person_set_collection("phenotype")
    assert psc is not None

    genotype_helper = GenotypeHelper(f1_trio, psc)
    # children_stats = genotype_helper.get_children_stats("phenotype1")
    children_by_sex = genotype_helper.children_by_sex("phenotype1")

    enrichment_events = event_counter.events(
        variants, children_by_sex, set(["missense", "synonymous"])
    )

    assert enrichment_events.all is not None
    assert len(enrichment_events.all) == 2
    assert enrichment_events.all == [["SAMD11"], ["SAMD11"]]

    assert enrichment_events.rec is not None
    assert len(enrichment_events.rec) == 1
    assert enrichment_events.rec == [["SAMD11"]]

    assert enrichment_events.male is not None
    assert len(enrichment_events.male) == 1
    assert enrichment_events.male == [["SAMD11"]]

    assert enrichment_events.female is not None
    assert len(enrichment_events.female) == 1
    assert enrichment_events.female == [["SAMD11"]]

    assert enrichment_events.unspecified is not None
    assert len(enrichment_events.unspecified) == 0

    result = f1_trio_coding_len_background.calc_enrichment_test(
        enrichment_events,
        ["SAMD11", "PLEKHN1", "POGZ"],
    )

    assert len(result["all"].events) == 2
    assert result["all"].expected == 2.0
    assert result["all"].pvalue == 1.0

    assert len(result["rec"].events) == 1
    assert result["rec"].expected == 1.0
    assert result["rec"].pvalue == 1.0

    assert len(result["male"].events) == 1
    assert result["male"].expected == 1.0
    assert result["male"].pvalue == 1.0

    assert len(result["female"].events) == 1
    assert result["female"].expected == 1.0
    assert result["female"].pvalue == 1.0

    assert len(result["unspecified"].events) == 0
    assert result["unspecified"].expected == 0.0
    assert result["unspecified"].pvalue == 1.0
