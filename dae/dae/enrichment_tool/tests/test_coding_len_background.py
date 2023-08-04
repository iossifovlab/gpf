# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Callable

import numpy as np
from box import Box

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
    genotype_helper = GenotypeHelper(f1_trio, psc)
    # children_stats = genotype_helper.get_children_stats("phenotype1")
    children_by_sex = genotype_helper.children_by_sex("phenotype1")

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

    result = f1_trio_coding_len_background.calc_stats(
        ["missense", "synonymous"],
        enrichment_events,
        ["SAMD11", "PLEKHN1", "POGZ"],
        children_by_sex,
    )

    assert result == enrichment_events

    assert result["all"].events is not None
    assert len(result["all"].events) == 2
    assert result["all"].events == [
        ["SAMD11"],
        ["SAMD11"],
    ]
    assert result["all"].expected == 2.0
    assert result["all"].pvalue == 1.0

    assert result["rec"].events is not None
    assert len(result["rec"].events) == 1
    assert result["rec"].events == [["SAMD11"]]
    assert result["rec"].expected == 1.0
    assert result["rec"].pvalue == 1.0

    assert result["male"].events is not None
    assert len(result["male"].events) == 1
    assert result["male"].events == [["SAMD11"]]
    assert result["male"].expected == 1.0
    assert result["male"].pvalue == 1.0

    assert result["female"].events is not None
    assert len(result["female"].events) == 1
    assert result["female"].events == [["SAMD11"]]
    assert result["female"].expected == 1.0
    assert result["female"].pvalue == 1.0

    assert result["unspecified"].events is not None
    assert len(result["unspecified"].events) == 0
    assert result["unspecified"].events == []
    assert result["unspecified"].expected is None
    assert result["unspecified"].pvalue is None


def test_use_cache(f1_trio_enrichment_config: Box) -> None:
    coding_len_background_without_cache = CodingLenBackground(
        f1_trio_enrichment_config
    )

    background = coding_len_background_without_cache.background

    assert coding_len_background_without_cache.is_ready is True
    coding_len_background_without_cache.load()
    bg1 = coding_len_background_without_cache.background
    assert np.all(background == bg1)
    assert coding_len_background_without_cache.is_ready is True

    coding_len_background = CodingLenBackground(f1_trio_enrichment_config)
    assert coding_len_background.is_ready is True
    coding_len_background.load()
    bg2 = coding_len_background.background
    assert np.all(background == bg2)
    assert np.all(bg1 == bg2)

    assert coding_len_background.is_ready is True
