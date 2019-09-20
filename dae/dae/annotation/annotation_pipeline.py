#!/usr/bin/env python

import os
import sys
import time
import datetime
import argparse
import subprocess

from box import Box

from dae.annotation.tools.annotator_base import AnnotatorBase, \
    CompositeVariantAnnotator
from dae.annotation.tools.annotator_config import AnnotationConfigParser
from dae.annotation.tools.file_io import IOType, IOManager
from dae.annotation.tools.annotator_config import annotation_config_cli_options
from dae.annotation.tools.utils import AnnotatorFactory

from dae.gpf_instance.gpf_instance import GPFInstance


def run_tabix(filename):
    def run_command(cmd):
        print('executing', cmd)
        try:
            subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as ex:
            status = ex.returncode
            output = ex.output

            print(status, output)
            raise Exception('FAILURE AT: ' + cmd)

    cmd = 'bgzip -c {filename} > {filename}.bgz'.format(
        filename=filename)
    run_command(cmd)

    cmd = 'tabix -s 1 -b 2 -e 2 -S 1 -f {filename}.bgz'.format(
        filename=filename)
    run_command(cmd)


class PipelineAnnotator(CompositeVariantAnnotator):

    def __init__(self, config):
        super(PipelineAnnotator, self).__init__(config)

    @staticmethod
    def build(options, config_file, work_dir, genomes_db, defaults=None):
        pipeline_config = \
            AnnotationConfigParser.read_and_parse_file_configuration(
                options, config_file, work_dir, genomes_db, defaults
            )
        assert pipeline_config.sections

        pipeline = PipelineAnnotator(pipeline_config)
        for section_config in pipeline_config.sections:
            annotator = AnnotatorFactory.make_annotator(section_config)
            pipeline.add_annotator(annotator)
            output_columns = [
                col for col in annotator.config.output_columns
                if col not in pipeline.config.output_columns
            ]
            pipeline.config.output_columns.extend(output_columns)
        return pipeline

    def add_annotator(self, annotator):
        assert isinstance(annotator, AnnotatorBase)
        self.config.virtual_columns.extend(annotator.config.virtual_columns)
        self.annotators.append(annotator)

    def line_annotation(self, aline):
        self.variant_builder.build(aline)
        for annotator in self.annotators:
            annotator.line_annotation(aline)

    def collect_annotator_schema(self, schema):
        super(PipelineAnnotator, self).collect_annotator_schema(schema)
        if self.config.virtual_columns:
            for vcol in self.config.virtual_columns:
                schema.remove_column(vcol)


def main_cli_options(gpf_instance):
    options = annotation_config_cli_options(gpf_instance)
    options.extend([
        ('infile', {
            'nargs': '?',
            'action': 'store',
            'default': '-',
            'help': 'path to input file; defaults to stdin '
            '[default: %(default)s]'
        }),
        ('outfile', {
            'nargs': '?',
            'action': 'store',
            'default': '-',
            'help': 'path to output file; defaults to stdout '
            '[default: %(default)s]'
        }),
        ('--region', {
            'help': 'work only in the specified region '
            '[default: %(default)s]',
            'default': None,
            'action': 'store'
        }),
        ('--read-parquet', {
            'help': 'read from a parquet file [default: %(default)s]',
            'action': 'store_true',
            'default': False,
        }),
        ('--write-parquet', {
            'help': 'write to a parquet file [default: %(default)s]',
            'action': 'store_true',
            'default': False,
        }),
        ('--notabix', {
            'help': 'skip running bgzip and tabix on the annotated files '
            '[default: %(default)s]',
            'default': False,
            'action': 'store_true',
        }),
        ('--mode', {
            'help': 'annotator mode; available modes are '
            '`replace` and `append` [default: %(default)s]',
            'default': '"replace"',
            'action': 'store'
        }),
    ])
    return options


def pipeline_main(argv):
    gpf_instance = GPFInstance()
    dae_config = gpf_instance.dae_config
    genomes_db = gpf_instance.genomes_db

    desc = 'Program to annotate variants combining multiple annotating tools'
    parser = argparse.ArgumentParser(
        description=desc, conflict_handler='resolve',
        formatter_class=argparse.RawDescriptionHelpFormatter)

    for name, args in main_cli_options(gpf_instance):
        parser.add_argument(name, **args)

    options = parser.parse_args()
    if options.annotation_config is not None:
        config_filename = options.annotation_config
    else:
        config_filename = dae_config.annotation.conf_file

    assert os.path.exists(config_filename), config_filename

    options = Box({
        k: v for k, v in options._get_kwargs()
    }, default_box=True, default_box_attr=None)

    # File IO format specification
    reader_type = IOType.TSV
    writer_type = IOType.TSV
    if options.read_parquet:
        reader_type = IOType.Parquet
    if options.write_parquet:
        writer_type = IOType.Parquet

    start = time.time()

    pipeline = PipelineAnnotator.build(
        options, config_filename, dae_config.dae_data_dir, genomes_db,
        defaults={'values': dae_config.annotation_defaults})
    assert pipeline is not None

    with IOManager(options, reader_type, writer_type) as io_manager:
        pipeline.annotate_file(io_manager)

    print('# PROCESSING DETAILS:', file=sys.stderr)
    print('#', time.asctime(), file=sys.stderr)
    print('#', ' '.join(sys.argv[1:]), file=sys.stderr)

    print(
        'The program was running for [h:m:s]:',
        str(datetime.timedelta(seconds=round(time.time()-start, 0))),
        file=sys.stderr)

    if not options.notabix:
        run_tabix(options.outfile)


if __name__ == '__main__':
    pipeline_main(sys.argv)
