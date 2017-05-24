'''
Created on May 24, 2017

@author: lubo
'''
import ConfigParser


def config_pheno_db(output):
    config = ConfigParser.SafeConfigParser()
    config.add_section('cache_dir')
    config.set('cache_dir', 'dir', '.')
    config.add_section('output')
    config.set('output', 'cache_file', output)

    config.add_section('continuous')
    config.set('continuous', 'min_individuals', '20')
    config.set('continuous', 'min_rank', '15')

    config.add_section('ordinal')
    config.set('ordinal', 'min_individuals', '20')
    config.set('ordinal', 'min_rank', '5')
    config.set('ordinal', 'max_rank', '17')

    config.add_section('categorical')
    config.set('categorical', 'min_individuals', '20')
    config.set('categorical', 'min_rank', '2')
    config.set('categorical', 'max_rank', '17')

    return config
