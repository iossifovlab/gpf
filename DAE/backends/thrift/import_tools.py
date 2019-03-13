from __future__ import print_function, absolute_import

import sys
import time
import os

from box import Box

from annotation.tools.file_io_parquet import ParquetSchema
from annotation.tools.annotator_config import AnnotatorConfig
from annotation.annotation_pipeline import PipelineAnnotator

from backends.configure import Configure
from backends.thrift.parquet_io import VariantsParquetWriter, \
    save_ped_df_to_parquet


def variants_iterator_to_parquet(
        fvars, parquet_prefix, bucket_index=0, annotation_pipeline=None):
    if fvars.is_empty():
        print("empty bucket {} done".format(parquet_prefix), file=sys.stderr)
        return

    # if annotation_pipeline is not None:
    #     fvars.annot_df = annotation_pipeline.annotate_df(fvars.annot_df)

    parquet_config = Configure.from_prefix_parquet(parquet_prefix).parquet
    print("converting into ", parquet_config, file=sys.stderr)

    save_ped_df_to_parquet(fvars.ped_df, parquet_config.pedigree)

    start = time.time()

    annotation_schema = ParquetSchema()
    annotation_pipeline.collect_annotator_schema(annotation_schema)

    variants_writer = VariantsParquetWriter(
        fvars.full_variants_iterator(),
        annotation_schema=annotation_schema)

    variants_writer.save_variants_to_parquet(
        summary_filename=parquet_config.summary_variant,
        family_filename=parquet_config.family_variant,
        effect_gene_filename=parquet_config.effect_gene_variant,
        member_filename=parquet_config.member_variant,
        bucket_index=bucket_index)
    end = time.time()

    print("DONE: {} for {:.2f} sec".format(parquet_prefix, end-start),
          file=sys.stderr)


def construct_import_annotation_pipeline(dae_config, argv, defaults={}):
    if 'annotation_config' in 'argv' and argv.annotation_config is not None:
        config_filename = argv.annotation_config
    else:
        config_filename = dae_config.annotation_conf

    assert os.path.exists(config_filename), config_filename

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

    pipeline = PipelineAnnotator.build(
        options, config_filename, defaults=defaults)
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
