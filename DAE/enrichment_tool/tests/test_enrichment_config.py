from __future__ import unicode_literals

from box import Box

from enrichment_tool.tests.conftest import fixtures_dir

from enrichment_tool.config import EnrichmentConfig


def test_enrichment_cache_file(enrichment_config):
    assert enrichment_config.enrichment_cache_file('tool') == \
        fixtures_dir() + '/studies/quads_f1/enrichment-tool.pckl'


def test_enrichment_config_people_groups(enrichment_config):
    assert enrichment_config.people_groups == ['phenotype']


def test_enrichment_config_default_values(enrichment_config):
    assert enrichment_config.default_background_model == \
        'synonymousBackgroundModel'
    assert enrichment_config.default_counting_model == \
        'enrichmentGeneCounting'


def test_enrichment_config_effect_types(enrichment_config):
    assert enrichment_config.effect_types == ['LGDs', 'missense', 'synonymous']


def test_enrichment_config_backgrounds(enrichment_config):
    assert enrichment_config.selected_background_values == [
        'synonymousBackgroundModel',
        'codingLenBackgroundModel',
        'samochaBackgroundModel'
    ]

    assert len(enrichment_config.backgrounds) == 3

    synonymous_background_model = \
        enrichment_config.backgrounds['synonymousBackgroundModel']
    assert synonymous_background_model['name'] == 'synonymousBackgroundModel'
    assert synonymous_background_model['id'] == 'synonymousBackgroundModel'
    assert synonymous_background_model['filename'] is None
    assert synonymous_background_model['desc'] == 'Synonymous Background Model'

    coding_len_background_model = \
        enrichment_config.backgrounds['codingLenBackgroundModel']
    assert coding_len_background_model['name'] == 'codingLenBackgroundModel'
    assert coding_len_background_model['id'] == 'codingLenBackgroundModel'
    assert coding_len_background_model['filename'] == fixtures_dir() + \
        '/studies/quads_f1/enrichment/codingLenBackgroundModel.csv'
    assert coding_len_background_model['desc'] == 'Coding Len Background Model'

    samocha_background_model = \
        enrichment_config.backgrounds['samochaBackgroundModel']
    assert samocha_background_model['name'] == 'samochaBackgroundModel'
    assert samocha_background_model['id'] == 'samochaBackgroundModel'
    assert samocha_background_model['filename'] == fixtures_dir() + \
        '/studies/quads_f1/enrichment/samochaBackgroundModel.csv'
    assert samocha_background_model['desc'] == 'Samocha Background Model'


def test_enrichment_config_counting(enrichment_config):
    assert enrichment_config.selected_counting_values == [
        'enrichmentEventsCounting',
        'enrichmentGeneCounting',
    ]

    assert len(enrichment_config.counting) == 2

    enrichment_events_counting = \
        enrichment_config.counting['enrichmentEventsCounting']
    assert enrichment_events_counting['name'] == 'enrichmentEventsCounting'
    assert enrichment_events_counting['id'] == 'enrichmentEventsCounting'
    assert enrichment_events_counting['filename'] is None
    assert enrichment_events_counting['desc'] == 'Enrichment Events Counting'

    enrichment_gene_counting = \
        enrichment_config.counting['enrichmentGeneCounting']
    assert enrichment_gene_counting['name'] == 'enrichmentGeneCounting'
    assert enrichment_gene_counting['id'] == 'enrichmentGeneCounting'
    assert enrichment_gene_counting['filename'] is None
    assert enrichment_gene_counting['desc'] == 'Enrichment Gene Counting'


def test_enrichment_config_empty():
    config = Box({
        'study_config': {
            'enrichment': {
                'enabled': False
            }
        }
    })

    assert EnrichmentConfig.from_config(config) is None

    config.study_config.enrichment = None
    assert EnrichmentConfig.from_config(config) is None

    config.study_config = None
    assert EnrichmentConfig.from_config(config) is None

    assert EnrichmentConfig.from_config(None) is None
