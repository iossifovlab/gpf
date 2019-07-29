#!/usr/bin/env python

import os
import sys
import time
import datetime
import re
import argparse
import subprocess

from box import Box
from ast import literal_eval
from configparser import ConfigParser
from collections import OrderedDict

import common.config
from annotation.tools.annotator_base import AnnotatorBase, \
    CompositeVariantAnnotator
from annotation.tools.annotator_config import VariantAnnotatorConfig
from annotation.tools.file_io import IOType, IOManager

from configurable_entities.configuration import DAEConfig


class PipelineConfig(VariantAnnotatorConfig):

    def __init__(self, name, annotator_name, options,
                 columns_config, virtuals):
        super(PipelineConfig, self).__init__(
            name, annotator_name, options,
            columns_config, virtuals
        )
        self.pipeline_sections = []
        self.optionxform = str

    @staticmethod
    def build(options, config_file, defaults={}):
        configuration = PipelineConfig._parse_pipeline_config(
            config_file, defaults
        )

        result = PipelineConfig(
            name="pipeline",
            annotator_name="annotation_pipeline.Pipeline",
            options=options,
            columns_config=OrderedDict(),
            virtuals=[]
        )
        result.pipeline_sections = []

        for section_name, section_config in configuration.items():
            section_config = result._parse_config_section(
                section_name, section_config, options)
            result.pipeline_sections.append(section_config)
        return result

    @staticmethod
    def _parse_pipeline_config(filename, defaults={}):
        class PipelineConfigParser(ConfigParser):
            """Modified ConfigParser.SafeConfigParser that
            allows ':' in keys and only '=' as separator.
            """
            OPTCRE = re.compile(
                r'(?P<option>[^=\s][^=]*)'          # allow only =
                r'\s*(?P<vi>[=])\s*'                # for option separator
                r'(?P<value>.*)$'
                )
            optionxform = str

        config_parser = PipelineConfigParser(defaults=defaults)

        with open(filename, "r", encoding="utf8") as infile:
            config_parser.read_file(infile)
            config = common.config.to_dict(config_parser)
        return config

    @staticmethod
    def _parse_config_section(section_name, section, options):
        # section = Box(section, default_box=True, default_box_attr=None)
        assert 'annotator' in section, [section_name, section]

        annotator_name = section['annotator']
        options = dict(options.to_dict())
        if 'options' in section:
            for key, val in section['options'].items():
                try:
                    val = literal_eval(val)
                except Exception:
                    pass
                options[key] = val

        options = Box(options, default_box=True, default_box_attr=None)

        if 'columns' in section:
            columns_config = OrderedDict(section['columns'])
        else:
            columns_config = OrderedDict()

        if 'virtuals' not in section:
            virtuals = []
        else:
            virtuals = [
                c.strip() for c in section['virtuals'].split(',')
            ]
        return VariantAnnotatorConfig(
            name=section_name,
            annotator_name=annotator_name,
            options=options,
            columns_config=columns_config,
            virtuals=virtuals
        )

    @staticmethod
    def cli_options(dae_config):
        options = [
            ('--config', {
                'help': 'config file location; default is "annotation.conf" '
                'in the instance data directory $DAE_DB_DIR '
                '[default: %(default)s]',
                'default': dae_config.annotation_conf,
                'action': 'store'
            }),
        ]
        options.extend(VariantAnnotatorConfig.cli_options(dae_config))
        return options


def run_tabix(filename):
    def run_command(cmd):
        print("executing", cmd)
        try:
            subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as ex:
            status = ex.returncode
            output = ex.output

            print(status, output)
            raise Exception("FAILURE AT: " + cmd)

    cmd = "bgzip -c {filename} > {filename}.bgz".format(
        filename=filename)
    run_command(cmd)

    cmd = "tabix -s 1 -b 2 -e 2 -S 1 -f {filename}.bgz".format(
        filename=filename)
    run_command(cmd)


class PipelineAnnotator(CompositeVariantAnnotator):

    def __init__(self, config):
        super(PipelineAnnotator, self).__init__(config)

    @staticmethod
    def build(options, config_file, defaults={}):
        pipeline_config = PipelineConfig.build(options, config_file, defaults)
        assert pipeline_config.pipeline_sections

        pipeline = PipelineAnnotator(pipeline_config)
        for section_config in pipeline_config.pipeline_sections:
            annotator = VariantAnnotatorConfig.instantiate(
                section_config
            )
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


def main_cli_options(dae_config):
    options = PipelineConfig.cli_options(dae_config)
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
    dae_config = DAEConfig.make_config()

    desc = "Program to annotate variants combining multiple annotating tools"
    parser = argparse.ArgumentParser(
        description=desc, conflict_handler='resolve',
        formatter_class=argparse.RawDescriptionHelpFormatter)

    for name, args in main_cli_options(dae_config):
        parser.add_argument(name, **args)

    options = parser.parse_args()
    if options.config is not None:
        config_filename = options.config
    else:
        config_filename = dae_config.annotation_conf

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
        options, config_filename, defaults=dae_config.annotation_defaults)
    assert pipeline is not None

    with IOManager(options, reader_type, writer_type) as io_manager:
        pipeline.annotate_file(io_manager)

    print("# PROCESSING DETAILS:", file=sys.stderr)
    print("#", time.asctime(), file=sys.stderr)
    print("#", " ".join(sys.argv[1:]), file=sys.stderr)

    print(
        "The program was running for [h:m:s]:",
        str(datetime.timedelta(seconds=round(time.time()-start, 0))),
        file=sys.stderr)

    if not options.notabix:
        run_tabix(options.outfile)


if __name__ == '__main__':
    pipeline_main(sys.argv)
