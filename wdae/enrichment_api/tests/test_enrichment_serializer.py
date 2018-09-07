'''
Created on May 11, 2017

@author: lubo
'''
from enrichment_api.enrichment_serializer import EnrichmentSerializer
from enrichment_api.views import EnrichmentModelsMixin
from datasets.config import DatasetsConfig
from datasets.datasets_factory import DatasetsFactory
from enrichment_api.enrichment_builder import EnrichmentBuilder


def test_enrichment_serializer_experiment():
    model = EnrichmentModelsMixin().get_enrichment_model({})
    config = DatasetsConfig()
    factory = DatasetsFactory(config)
    dataset = factory.get_dataset('SD_TEST')
    builder = EnrichmentBuilder(dataset, model, ['POGZ'])
    results = builder.build()

    serializer = EnrichmentSerializer(results)
    effect_types = serializer.build_effect_types_naming(['synonymous'])

    assert ['Synonymous'] == effect_types
