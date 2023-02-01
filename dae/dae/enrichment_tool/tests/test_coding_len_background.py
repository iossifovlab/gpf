# pylint: disable=W0621,C0114,C0116,W0212,W0613
import numpy as np

from dae.variants.attributes import Inheritance

from dae.enrichment_tool.background import CodingLenBackground
from dae.enrichment_tool.event_counters import EventsCounter
from dae.enrichment_tool.genotype_helper import GenotypeHelper


def test_filename(f1_trio_coding_len_background, fixture_dirname):
    assert f1_trio_coding_len_background.filename == fixture_dirname(
        "studies/f1_trio/enrichment/codingLenBackgroundModel.csv"
    )


def test_load(f1_trio_coding_len_background):
    background = f1_trio_coding_len_background.load()

    assert len(background) == 3
    assert background.iloc[0]["sym"] == "SAMD11"
    assert background.iloc[0]["raw"] == 3
    assert background.iloc[1]["sym"] == "PLEKHN1"
    assert background.iloc[1]["raw"] == 7
    assert background.iloc[2]["sym"] == "POGZ"
    assert background.iloc[2]["raw"] == 13


def test_calc_stats(f1_trio, f1_trio_coding_len_background):
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
    children_stats = genotype_helper.get_children_stats("phenotype1")
    children_by_sex = genotype_helper.children_by_sex("phenotype1")

    enrichment_events = event_counter.events(
        variants, children_by_sex, set(["missense", "synonymous"])
    )

    assert len(enrichment_events["all"].events) == 2
    assert enrichment_events["all"].events == [["SAMD11"], ["SAMD11"]]
    assert enrichment_events["all"].expected is None
    assert enrichment_events["all"].pvalue is None
    assert len(enrichment_events["rec"].events) == 1
    assert enrichment_events["rec"].events == [["SAMD11"]]
    assert enrichment_events["rec"].expected is None
    assert enrichment_events["rec"].pvalue is None
    assert len(enrichment_events["male"].events) == 1
    assert enrichment_events["male"].events == [["SAMD11"]]
    assert enrichment_events["male"].expected is None
    assert enrichment_events["male"].pvalue is None
    assert len(enrichment_events["female"].events) == 1
    assert enrichment_events["female"].events == [["SAMD11"]]
    assert enrichment_events["female"].expected is None
    assert enrichment_events["female"].pvalue is None
    assert len(enrichment_events["unspecified"].events) == 0
    assert enrichment_events["unspecified"].events == []
    assert enrichment_events["unspecified"].expected is None
    assert enrichment_events["unspecified"].pvalue is None

    ee = f1_trio_coding_len_background.calc_stats(
        ["missense", "synonymous"],
        enrichment_events,
        ["SAMD11", "PLEKHN1", "POGZ"],
        children_stats,
    )

    assert ee == enrichment_events

    assert len(ee["all"].events) == 2
    assert ee["all"].events == [
        ["SAMD11"],
        ["SAMD11"],
    ]
    assert ee["all"].expected == 2.0
    assert ee["all"].pvalue == 1.0
    assert len(ee["rec"].events) == 1
    assert ee["rec"].events == [["SAMD11"]]
    assert ee["rec"].expected == 1.0
    assert ee["rec"].pvalue == 1.0
    assert len(ee["male"].events) == 1
    assert ee["male"].events == [["SAMD11"]]
    assert ee["male"].expected == 1.0
    assert ee["male"].pvalue == 1.0
    assert len(ee["female"].events) == 1
    assert ee["female"].events == [["SAMD11"]]
    assert ee["female"].expected == 1.0
    assert ee["female"].pvalue == 1.0
    assert len(ee["unspecified"].events) == 0
    assert ee["unspecified"].events == []
    assert ee["unspecified"].expected is None
    assert ee["unspecified"].pvalue is None


def test_use_cache(f1_trio_enrichment_config):
    coding_len_background_without_cache = CodingLenBackground(
        f1_trio_enrichment_config
    )

    background = coding_len_background_without_cache.background

    assert coding_len_background_without_cache.is_ready is True
    b1 = coding_len_background_without_cache.load()
    assert np.all(background == b1)
    assert coding_len_background_without_cache.is_ready is True

    coding_len_background = CodingLenBackground(f1_trio_enrichment_config)

    assert coding_len_background.is_ready is True

    b2 = coding_len_background.load()
    assert np.all(background == b2)
    assert np.all(b1 == b2)

    assert coding_len_background.is_ready is True


def test_effects(f1_trio):
    vs = f1_trio.query_variants()
    for v in vs:
        print(30 * "-")
        print(v, v.effects)
        for fa in v.alleles:
            print("\t", fa, fa.effects)


# def test_effects_annotate(f1_trio):
#     loader = f1_trio._backend.variants_loaders[0]
#     print(loader.filenames)
#     annotation_filename = StoredAnnotationDecorator\
#           .build_annotation_filename(
#               loader.filenames[0]
#           )
#     annotation_filename += '_new'

#     print(loader.filenames[0], annotation_filename)

#     StoredAnnotationDecorator.save_annotation_file(
#         loader, annotation_filename)
