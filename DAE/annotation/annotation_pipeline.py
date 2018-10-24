#!/usr/bin/env python

from __future__ import print_function
from builtins import open

import os
import sys
import time
import datetime
import re
import argparse

from box import Box
from ast import literal_eval
from configparser import ConfigParser
from collections import OrderedDict

import common.config
from annotation.tools.annotator_base import CompositeVariantAnnotator
from annotation.tools.annotator_config import VariantAnnotatorConfig
from annotation.tools.file_io import IOType, IOManager


class PipelineConfig(VariantAnnotatorConfig):

    def __init__(self, name, annotator_name, options,
                 columns_config, virtuals):
        super(PipelineConfig, self).__init__(
            name, annotator_name, options,
            columns_config, virtuals
        )
        self.pipeline_sections = []

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

        config_parser = PipelineConfigParser(defaults=defaults)

        config_parser.optionxform = str
        with open(filename, "r", encoding="utf8") as infile:
            config_parser.read_file(infile)
            config = common.config.to_dict(config_parser)
        return config

    @staticmethod
    def _parse_config_section(section_name, section, options):
        # section = Box(section, default_box=True, default_box_attr=None)
        assert 'annotator' in section

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


def pipeline_main(argv):
    desc = "Program to annotate variants combining multiple annotating tools"
    parser = argparse.ArgumentParser(
        description=desc, conflict_handler='resolve')
    parser.add_argument(
        '--config', help='config file location',
        required=True, action='store')

    for name, args in VariantAnnotatorConfig.cli_options():
        parser.add_argument(name, **args)

    options = parser.parse_args()
    assert options.config is not None
    assert os.path.exists(options.config)
    config_filename = options.config

    options = Box({
        k: v for k, v in options._get_kwargs()
    }, default_box=True, default_box_attr=None)

    pipeline = PipelineAnnotator.build(options, config_filename)
    assert pipeline is not None

    # File IO format specification
    reader_type = IOType.TSV
    writer_type = IOType.TSV
    if hasattr(options, 'read_parquet'):
        if options.read_parquet:
            reader_type = IOType.Parquet
    if hasattr(options, 'write_parquet'):
        if options.write_parquet:
            writer_type = IOType.Parquet

    start = time.time()

    with IOManager(options, reader_type, writer_type) as io_manager:
        pipeline.annotate_file(io_manager)

    print("# PROCESSING DETAILS:", file=sys.stderr)
    print("#", time.asctime(), file=sys.stderr)
    print("#", " ".join(sys.argv[1:]), file=sys.stderr)

    print(
        "The program was running for [h:m:s]:",
        str(datetime.timedelta(seconds=round(time.time()-start, 0))),
        file=sys.stderr)


if __name__ == '__main__':
    pipeline_main(sys.argv)
