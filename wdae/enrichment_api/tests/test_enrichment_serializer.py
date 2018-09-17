'''
Created on May 11, 2017

@author: lubo
'''
from enrichment_api.enrichment_serializer import EnrichmentSerializer
from enrichment_api.views import EnrichmentModelsMixin
from datasets.dataset_config import DatasetConfig
from datasets.dataset_factory import DatasetFactory
from enrichment_api.enrichment_builder import EnrichmentBuilder


def test_enrichment_serializer_experiment():
    model = EnrichmentModelsMixin().get_enrichment_model({})
    config = DatasetConfig()
    factory = DatasetFactory()
    dataset = factory.make_dataset(config)
    builder = EnrichmentBuilder(dataset, model, ['POGZ'])
    results = builder.build()

    serializer = EnrichmentSerializer(results)
    effect_types = serializer.build_effect_types_naming(['synonymous'])

    assert ['Synonymous'] == effect_types
