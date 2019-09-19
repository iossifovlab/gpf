import pytest

from dae.variants.attributes import Inheritance

from dae.enrichment_tool.tests.conftest import fixtures_dir

from dae.enrichment_tool.event_counters import EventsCounter
from dae.enrichment_tool.genotype_helper import GenotypeHelper


def test_filename(f1_trio_samocha_background):
    assert f1_trio_samocha_background.filename == fixtures_dir() + \
        '/studies/f1_trio/enrichment/samochaBackgroundModel.csv'


def test_load(f1_trio_samocha_background):
    background = f1_trio_samocha_background.load()

    assert len(background) == 3

    assert background.iloc[0]['gene'] == 'SAMD11'
    assert background.iloc[0]['F'] == 2
    assert background.iloc[0]['M'] == 2
    assert background.iloc[0]['P_LGDS'] == 1.1
    assert background.iloc[0]['P_MISSENSE'] == 1.4
    assert background.iloc[0]['P_SYNONYMOUS'] == 5.7

    assert background.iloc[1]['gene'] == 'PLEKHN1'
    assert background.iloc[1]['F'] == 2
    assert background.iloc[1]['M'] == 2
    assert background.iloc[1]['P_LGDS'] == 1.2
    assert background.iloc[1]['P_MISSENSE'] == 1.5
    assert background.iloc[1]['P_SYNONYMOUS'] == 5.8

    assert background.iloc[2]['gene'] == 'POGZ'
    assert background.iloc[2]['F'] == 2
    assert background.iloc[2]['M'] == 2
    assert background.iloc[2]['P_LGDS'] == 6.3
    assert background.iloc[2]['P_MISSENSE'] == 4.6
    assert background.iloc[2]['P_SYNONYMOUS'] == 2.9


def test_calc_stats(f1_trio, f1_trio_samocha_background):
    variants = list(f1_trio.query_variants(
        inheritance=str(Inheritance.denovo.name)))
    event_counter = EventsCounter()

    pg = f1_trio.get_people_group('phenotype')
    gh = GenotypeHelper(f1_trio, pg, 'autism')
    children_stats = gh.get_children_stats()
    children_by_sex = gh.children_by_sex()

    enrichment_events = event_counter.events(
        variants, children_by_sex, set(['missense', 'synonymous']))

    assert len(enrichment_events['all'].events) == 2
    assert enrichment_events['all'].events == \
        [['SAMD11'], ['SAMD11']]
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
    assert len(enrichment_events['female'].events) == 1
    assert enrichment_events['female'].events == [['SAMD11']]
    assert enrichment_events['female'].expected is None
    assert enrichment_events['female'].pvalue is None
    assert len(enrichment_events['unspecified'].events) == 0
    assert enrichment_events['unspecified'].events == []
    assert enrichment_events['unspecified'].expected is None
    assert enrichment_events['unspecified'].pvalue is None

    ee = f1_trio_samocha_background.calc_stats(
        'missense', enrichment_events,
        ['SAMD11', 'PLEKHN1', 'POGZ'], children_by_sex)

    assert ee == enrichment_events

    assert len(ee['all'].events) == 2
    assert ee['all'].events == [['SAMD11'], ['SAMD11']]
    assert ee['all'].expected == 30.0
    assert ee['all'].pvalue == pytest.approx(9.002e-11)
    assert len(ee['rec'].events) == 1
    assert ee['rec'].events == [['SAMD11']]
    assert ee['rec'].expected == 15.0
    assert ee['rec'].pvalue == pytest.approx(9.788e-6, rel=1e-3)
    assert len(ee['male'].events) == 1
    assert ee['male'].events == [['SAMD11']]
    assert ee['male'].expected == 15.0
    assert ee['male'].pvalue == pytest.approx(9.788e-06, rel=1e-3)
    assert len(ee['female'].events) == 1
    assert ee['female'].events == [['SAMD11'],]
    assert ee['female'].expected == 15.0
    assert ee['female'].pvalue == pytest.approx(9.788e-06, rel=1e-3)
    assert len(ee['unspecified'].events) == 0
    assert ee['unspecified'].events == []
    assert ee['unspecified'].expected is None
    assert ee['unspecified'].pvalue is None
