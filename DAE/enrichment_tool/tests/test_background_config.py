'''
Created on Nov 7, 2016

@author: lubo
'''
from __future__ import unicode_literals
from enrichment_tool.background import BackgroundConfig


def test_background_config_default():
    conf = BackgroundConfig()
    assert conf['enrichment', 'backgrounds'] is not None


def test_background_config_backgrounds():
    conf = BackgroundConfig()
    assert conf.backgrounds is not None


def test_background_config_backgrounds_contains_synonymous_model():
    conf = BackgroundConfig()
    assert conf.backgrounds is not None

    assert 'synonymousBackgroundModel' in conf.backgrounds


def test_background_config_backgrounds_cache_dir():
    conf = BackgroundConfig()
    assert conf.cache_dir is not None
