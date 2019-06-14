from __future__ import print_function, absolute_import

import os

from box import Box

from annotation.tools.annotator_config import AnnotatorConfig
from annotation.annotation_pipeline import PipelineAnnotator


def construct_import_annotation_pipeline(dae_config, argv=None, defaults={}):

    if argv is not None and 'annotation_config' in argv and \
            argv.annotation_config is not None:
        config_filename = argv.annotation_config
    else:
        config_filename = dae_config.annotation_conf

    assert os.path.exists(config_filename), config_filename
    options = {}
    if argv is not None:
        options = {
            k: v for k, v in argv._get_kwargs()
        }
    options.update({
        "vcf": True,
        'c': 'chrom',
        'p': 'position',
        'r': 'reference',
        'a': 'alternative',
    })
    options = Box(options, default_box=True, default_box_attr=None)

    annotation_defaults = dae_config.annotation_defaults
    annotation_defaults.update(defaults)

    pipeline = PipelineAnnotator.build(
        options, config_filename, defaults=annotation_defaults)
    return pipeline


def annotation_pipeline_cli_options(dae_config):
    options = []
    options.extend([
        ('--annotation', {
            'help': 'config file location; default is "annotation.conf" '
            'in the instance data directory $DAE_DB_DIR '
            '[default: %(default)s]',
            'default': dae_config.annotation_conf,
            'action': 'store',
            'dest': 'annotation_config',
        }),
    ])
    options.extend(
        AnnotatorConfig.cli_options(dae_config)
    )
    return options
