'''
Created on Nov 7, 2016

@author: lubo
'''
from gene_weights.weights import WeightsConfig


def test_weights_config_common():
    conf = WeightsConfig()
    assert conf is not None

    assert conf['geneWeights.RVIS_rank', 'file'] is not None
    print(conf['geneWeights.RVIS_rank', 'file'])


# def test_weights_description():
#     conf = WeightsConfig()
#
#     assert conf['geneWeights', 'desc'] is not None
#
#     assert conf.desc is not None
