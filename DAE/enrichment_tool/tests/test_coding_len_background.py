import io
import zlib
import numpy as np

from variants.attributes import Inheritance

from enrichment_tool.tests.conftest import fixtures_dir

from enrichment_tool.background import CodingLenBackground
from enrichment_tool.event_counters import EventsCounter
from enrichment_tool.genotype_helper import GenotypeHelper


def test_filename(f1_trio_coding_len_background):
    assert f1_trio_coding_len_background.filename == fixtures_dir() + \
        '/studies/f1_trio/enrichment/codingLenBackgroundModel.csv'


def test_precompute(f1_trio_coding_len_background):
    background = f1_trio_coding_len_background.precompute()

    assert len(background) == 3
    assert background[0]['sym'] == 'SAMD11'
    assert background[0]['raw'] == 3
    assert background[1]['sym'] == 'PLEKHN1'
    assert background[1]['raw'] == 7
    assert background[2]['sym'] == 'POGZ'
    assert background[2]['raw'] == 13


def test_serialize(f1_trio_coding_len_background):
    f1_trio_coding_len_background.precompute()
    serialized = f1_trio_coding_len_background.serialize()

    assert len(serialized) == 1

    fin = io.BytesIO(zlib.decompress(serialized['background']))
    background = np.load(fin)

    assert len(background) == 3
    assert background[0]['sym'] == 'SAMD11'
    assert background[0]['raw'] == 3
    assert background[1]['sym'] == 'PLEKHN1'
    assert background[1]['raw'] == 7
    assert background[2]['sym'] == 'POGZ'
    assert background[2]['raw'] == 13


def test_deserialize(f1_trio_coding_len_background):
    f1_trio_coding_len_background.precompute()
    serialized = f1_trio_coding_len_background.serialize()
    f1_trio_coding_len_background.deserialize(serialized)
    background = f1_trio_coding_len_background.background

    assert len(background) == 3
    assert background[0]['sym'] == 'SAMD11'
    assert background[0]['raw'] == 3
    assert background[1]['sym'] == 'PLEKHN1'
    assert background[1]['raw'] == 7
    assert background[2]['sym'] == 'POGZ'
    assert background[2]['raw'] == 13


def test_calc_stats(f1_trio, f1_trio_coding_len_background):
    variants = list(f1_trio.query_variants(
        inheritance=str(Inheritance.denovo.name)))
    event_counter = EventsCounter()
    enrichment_events = event_counter.events(variants)

    pg = f1_trio.config.people_group_config.get_people_group('phenotype')
    gh = GenotypeHelper(f1_trio, pg, 'autism')
    children_stats = gh.get_children_stats()

    assert len(enrichment_events['all'].events) == 3
    assert enrichment_events['all'].events == \
        [['SAMD11'], ['SAMD11'], ['PLEKHN1']]
    assert enrichment_events['all'].expected is None
    assert enrichment_events['all'].pvalue is None
    assert len(enrichment_events['rec'].events) == 1
    assert enrichment_events['rec'].events == [['SAMD11']]
    assert enrichment_events['rec'].expected is None
    assert enrichment_events['rec'].pvalue is None
    assert len(enrichment_events['male'].events) == 1
    assert enrichment_events['male'].events == [['SAMD11']]
    assert enrichment_events['male'].expected is None
    assert enrichment_events['male'].pvalue is None
    assert len(enrichment_events['female'].events) == 2
    assert enrichment_events['female'].events == [['SAMD11'], ['PLEKHN1']]
    assert enrichment_events['female'].expected is None
    assert enrichment_events['female'].pvalue is None
    assert len(enrichment_events['unspecified'].events) == 0
    assert enrichment_events['unspecified'].events == []
    assert enrichment_events['unspecified'].expected is None
    assert enrichment_events['unspecified'].pvalue is None

    ee = f1_trio_coding_len_background.calc_stats(
        ['missense', 'synonymous'], enrichment_events,
        ['SAMD11', 'PLEKHN1', 'POGZ'], children_stats)

    assert ee == enrichment_events

    assert len(ee['all'].events) == 3
    assert ee['all'].events == [['SAMD11'], ['SAMD11'], ['PLEKHN1']]
    assert ee['all'].expected == 3.0
    assert ee['all'].pvalue == 1.0
    assert len(ee['rec'].events) == 1
    assert ee['rec'].events == [['SAMD11']]
    assert ee['rec'].expected == 1.0
    assert ee['rec'].pvalue == 1.0
    assert len(ee['male'].events) == 1
    assert ee['male'].events == [['SAMD11']]
    assert ee['male'].expected == 1.0
    assert ee['male'].pvalue == 1.0
    assert len(ee['female'].events) == 2
    assert ee['female'].events == [['SAMD11'], ['PLEKHN1']]
    assert ee['female'].expected == 2.0
    assert ee['female'].pvalue == 1.0
    assert len(ee['unspecified'].events) == 0
    assert ee['unspecified'].events == []
    assert ee['unspecified'].expected is None
    assert ee['unspecified'].pvalue is None


def test_use_cache(f1_trio_enrichment_config):
    coding_len_background_without_cache = CodingLenBackground(
        f1_trio_enrichment_config)

    coding_len_background_without_cache.cache_clear()

    assert coding_len_background_without_cache.is_ready is True
    assert coding_len_background_without_cache.cache_load() is False
    assert coding_len_background_without_cache.cache_clear() is False
    assert coding_len_background_without_cache.is_ready is True

    coding_len_background = CodingLenBackground(
        f1_trio_enrichment_config, use_cache=True)

    assert coding_len_background.is_ready is True

    assert coding_len_background.cache_load() is True
    assert coding_len_background.cache_clear() is True
    assert coding_len_background.cache_clear() is False

    assert coding_len_background.is_ready is True
