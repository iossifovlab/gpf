import pytest
from box import Box

from dae.enrichment_tool.tests.conftest import fixtures_dir

from dae.enrichment_tool.config import EnrichmentConfigParser
from dae.enrichment_tool.background import BackgroundBase


def test_enrichment_cache_file(f1_trio_enrichment_config):
    assert BackgroundBase.enrichment_cache_file(
        f1_trio_enrichment_config, 'tool') == \
            fixtures_dir() + '/studies/f1_trio/enrichment-tool.pckl'


def test_enrichment_config_people_groups(f1_trio_enrichment_config):
    enrichment_config = f1_trio_enrichment_config.enrichment
    assert enrichment_config.selected_people_groups == ['phenotype']


def test_enrichment_config_default_values(f1_trio_enrichment_config):
    enrichment_config = f1_trio_enrichment_config.enrichment
    assert enrichment_config.default_background_model == \
        'synonymousBackgroundModel'
    assert enrichment_config.default_counting_model == \
        'enrichmentGeneCounting'


def test_enrichment_config_effect_types(f1_trio_enrichment_config):
    enrichment_config = f1_trio_enrichment_config.enrichment
    assert enrichment_config.effect_types == \
        ['LGDs', 'missense', 'synonymous']


def test_enrichment_config_backgrounds(f1_trio_enrichment_config):
    enrichment_config = f1_trio_enrichment_config.enrichment
    assert enrichment_config.selected_background_values == [
        'synonymousBackgroundModel',
        'codingLenBackgroundModel',
        'samochaBackgroundModel'
    ]

    assert len(enrichment_config.background) == 3

    synonymous_background_model = \
        enrichment_config.background.synonymousBackgroundModel
    assert synonymous_background_model.name == 'synonymousBackgroundModel'
    assert synonymous_background_model.file is None
    assert synonymous_background_model.desc == 'Synonymous Background Model'

    coding_len_background_model = \
        enrichment_config.background.codingLenBackgroundModel
    assert coding_len_background_model.name == 'codingLenBackgroundModel'
    assert coding_len_background_model.file == fixtures_dir() + \
        '/studies/f1_trio/enrichment/codingLenBackgroundModel.csv'
    assert coding_len_background_model.desc == 'Coding Len Background Model'

    samocha_background_model = \
        enrichment_config.background.samochaBackgroundModel
    assert samocha_background_model.name == 'samochaBackgroundModel'
    assert samocha_background_model.file == fixtures_dir() + \
        '/studies/f1_trio/enrichment/samochaBackgroundModel.csv'
    assert samocha_background_model.desc == 'Samocha Background Model'


def test_enrichment_config_counting(f1_trio_enrichment_config):
    enrichment_config = f1_trio_enrichment_config.enrichment
    assert enrichment_config.selected_counting_values == [
        'enrichmentEventsCounting',
        'enrichmentGeneCounting',
    ]

    assert len(enrichment_config.counting) == 3
    assert len(
        list(filter(
            lambda x: x.name in enrichment_config.selected_counting_values,
            enrichment_config.counting)
        )
    ) == 2

    enrichment_events_counting = \
        enrichment_config.counting.enrichmentEventsCounting
    assert enrichment_events_counting.name == 'enrichmentEventsCounting'
    assert enrichment_events_counting.file is None
    assert enrichment_events_counting.desc == 'Enrichment Events Counting'

    enrichment_gene_counting = \
        enrichment_config.counting.enrichmentGeneCounting
    assert enrichment_gene_counting.name == 'enrichmentGeneCounting'
    assert enrichment_gene_counting.file is None
    assert enrichment_gene_counting.desc == 'Enrichment Gene Counting'


@pytest.mark.skip()
def test_enrichment_config_empty():
    config = Box({
        'study_config': {
            'enrichment': {
                'enabled': False
            },
            'config_file': '/conf/enrichement.conf'
        }
    })

    assert EnrichmentConfigParser.parse(config) is None

    config.study_config.enrichment = None
    assert EnrichmentConfigParser.parse(config) is None

    config.study_config = None
    assert EnrichmentConfigParser.parse(config) is None

    assert EnrichmentConfigParser.parse(None) is None
