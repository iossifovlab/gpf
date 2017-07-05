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

    config.add_section('individuals')
    config.set('individuals', 'min_individuals', '20')

    config.add_section('continuous')
    config.set('continuous', 'min_rank', '15')

    config.add_section('ordinal')
    config.set('ordinal', 'min_rank', '5')

    config.add_section('categorical')
    config.set('categorical', 'min_rank', '2')

    return config


def adjust_config_pheno_db(config, args):
    if args.min_individuals is not None and args.min_individuals >= 0:
        config.set('individuals', 'min_individuals', str(args.min_individuals))

    if args.categorical is not None and args.categorical >= 0:
        config.set('categorical', 'min_rank', str(args.categorical))

    if args.ordinal is not None and args.ordinal >= 0:
        config.set('ordinal', 'min_rank', str(args.ordinal))

    if args.continuous is not None and args.continuous >= 0:
        config.set('continuous', 'min_rank', str(args.continuous))

    return config


def check_config_pheno_db(config):
    categorical = int(config.get('categorical', 'min_rank'))
    if categorical < 1:
        print('categorical min rank expected to be > 0')
        return False
    ordinal = int(config.get('ordinal', 'min_rank'))
    if ordinal < categorical:
        print('ordianl min rank expected to be >= categorical min rank')
        return False
    continuous = int(config.get('continuous', 'min_rank'))
    if continuous < ordinal:
        print('continuous min rank expected to be >= ordinal min rank')
        return False

    individuals = int(config.get('individuals', 'min_individuals'))
    if individuals < 1:
        print('minimal number of individuals expected to be >= 1')
        return False

    return True


def dump_config(config):
    print("--------------------------------------------------------")
    print("CLASSIFICATION BOUNDARIES:")
    print("--------------------------------------------------------")
    print("min individuals:      {}".format(
        config.get('individuals', 'min_individuals')))
    print("continuous min rank:  {}".format(
        config.get('continuous', 'min_rank')))
    print("ordinal min rank:     {}".format(
        config.get('ordinal', 'min_rank')))
    print("categorical min rank: {}".format(
        config.get('categorical', 'min_rank')))
    print("--------------------------------------------------------")
