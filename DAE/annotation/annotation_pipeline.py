#!/usr/bin/env python

from __future__ import unicode_literals
from __future__ import print_function

import re

from box import Box
from ast import literal_eval
from configparser import ConfigParser
from collections import OrderedDict

import common.config
from annotation.tools.annotator_base import CompositeVariantAnnotator
from annotation.tools.annotator_config import VariantAnnotatorConfig


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
        print(config_parser.defaults())

        config_parser.optionxform = str
        with open(filename, "r", encoding="utf8") as infile:
            config_parser.read_file(infile)
            config = Box(
                common.config.to_dict(config_parser),
                default_box=True, default_box_attr=None)
        return config

    @staticmethod
    def _parse_config_section(section_name, section, options):
        assert section.annotator is not None
        annotator_name = section.annotator
        options = dict(options.to_dict())
        if section.options:
            for key, val in section.options.items():
                try:
                    val = literal_eval(val)
                except Exception:
                    pass
                options[key] = val

        options = Box(options, default_box=True, default_box_attr=None)

        columns_config = OrderedDict(section.columns)
        if section.virtuals is None:
            virtuals = []
        else:
            virtuals = [
                c.strip() for c in section.virtuals.split(',')
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

