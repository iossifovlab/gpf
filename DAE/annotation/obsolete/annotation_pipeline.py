#!/usr/bin/env python

from __future__ import print_function, unicode_literals, absolute_import

from future import standard_library
standard_library.install_aliases()  # noqa

import sys
import glob
import argparse

from builtins import object

from configparser import ConfigParser

import common.config
import re
# from os.path import exists, dirname, basename, realpath
import os
from box import Box
from importlib import import_module
from ast import literal_eval
from collections import OrderedDict
from functools import reduce
from annotation.tools.utilities import assign_values
from annotation.tools.utilities import main
from annotation.tools.utilities import AnnotatorBase
from annotation.tools import variant_format

from annotation.tools import *  # noqa


def str_to_class(val):
    return reduce(getattr, val.split("."), sys.modules[__name__])


class MyConfigParser(ConfigParser):
    """Modified ConfigParser.SafeConfigParser that
    allows ':' in keys and only '=' as separator.
    """
    OPTCRE = re.compile(
        r'(?P<option>[^=\s][^=]*)'          # allow only =
        r'\s*(?P<vi>[=])\s*'                # for option separator
        r'(?P<value>.*)$'
        )


class MultiAnnotator(AnnotatorBase):
    """
    `MultiAnnotator` class processes user passed options and annotates variant
    data. After processing of user options this class passes line by line the
    data to `Annotators` and `Preannotators`.
    """

    def __init__(self, opts, header=None):
        super(MultiAnnotator, self).__init__(opts, header)
        self.variant_format = variant_format.VariantFormatPreannotator(
            opts, header)
        self.preannotators = [self.variant_format]

        self.preannotators.extend(
            PreannotatorLoader.load_preannotators(opts, header))

        self.annotators = []
        virtual_columns_indices = []
        all_columns_labels = set()

        for preannotator in self.preannotators:
            self.annotators.append({
                'instance': preannotator,
                'columns': OrderedDict(
                    [(c, c) for c in preannotator.new_columns])
            })
            all_columns_labels.update(preannotator.new_columns)
            if self.header:
                self.header.extend(preannotator.new_columns)

            virtual_columns_indices.extend(
                [assign_values(column, self.header)
                    for column in preannotator.new_columns])

        extracted_options = []
        if opts.default_arguments is not None:
            for option in opts.default_arguments.split(','):
                split_options = option.split(':')
                try:
                    split_options[1] = literal_eval(split_options[1])
                except ValueError:
                    pass
                extracted_options.append(split_options)
        default_arguments = dict(extracted_options)

        if opts.config is None:
            print(
                "You should provide a config file location.", file=sys.stderr)
            assert False
            sys.exit(1)
        elif not os.path.exists(opts.config):
            print("The provided config file does not exist!", file=sys.stderr)
            assert False
            sys.exit(1)

        config_parser = MyConfigParser()
        config_parser.optionxform = str
        config_parser.read(opts.config)
        self.config = Box(common.config.to_dict(config_parser),
                          default_box=True, default_box_attr=None)

        # config_parser.sections() this gives the sections in order which
        # is important
        for annotation_step in config_parser.sections():
            annotation_step_config = self.config[annotation_step]

            for default_argument, value in default_arguments.items():
                if annotation_step_config.options[default_argument] is None:
                    annotation_step_config.options[default_argument] = value

            step_columns_labels = annotation_step_config.columns.values()
            all_columns_labels.update(step_columns_labels)

            if self.header is not None:
                if opts.append:
                    new_columns = step_columns_labels
                else:
                    new_columns = [column for column in step_columns_labels
                                   if column not in self.header]
                self.header.extend(new_columns)

            if annotation_step_config.virtuals is not None:
                virtual_columns_indices.extend(
                    [assign_values(
                        annotation_step_config.columns[column.strip()],
                        self.header)
                     for column in annotation_step_config.virtuals.split(',')])
            annotation_step_config.options.region = opts.region
            self.annotators.append({
                'instance': str_to_class(annotation_step_config.annotator)(
                    annotation_step_config.options, list(self.header)),
                'columns': annotation_step_config.columns
            })

        self.column_indices = {label: assign_values(label, self.header)
                               for label in all_columns_labels}
        self.stored_columns_indices = [
            i for i in range(1, len(self.header) + 1)
            if i not in virtual_columns_indices
        ]

    def line_annotations(self, line, new_columns):
        pass

    def annotate_file(self, file_io_manager):
        def annotate_line(line):

            for annotator in annotators:
                columns = annotator['columns'].keys()
                columns_labels = annotator['columns'].values()
                values = annotator['instance'].line_annotations(line, columns)
                for label, value in zip(columns_labels, values):
                    position = self.column_indices[label]
                    line[position - 1:position] = [value]
            return line

        if self.header:
            self.header = [self.header[i-1]
                           for i in self.stored_columns_indices]
            self.header[0] = '#' + self.header[0]
            file_io_manager.header_write(self.header)

        annotators = self.annotators

        for line in file_io_manager.lines_read():
            if '#' == line[0][0]:
                file_io_manager.line_write(line)
                continue

            annotated = annotate_line(line)

            file_io_manager.line_write([
                annotated[i-1] for i in self.stored_columns_indices
            ])


class PreannotatorLoader(object):
    """
    Class for finding and loading `Preannotators`. It imports preannotator
    classes from `annotation/preannotators` and stores them in list.

    It is used by `MultiAnnotator`.
    """

    PREANNOTATOR_MODULES = None

    @classmethod
    def get_preannotator_modules(cls):
        if cls.PREANNOTATOR_MODULES is None:
            abs_files = glob.glob(
                os.path.dirname(os.path.realpath(__file__)) +
                '/preannotators/*.py')
            files = [os.path.basename(f) for f in abs_files]
            files.remove('__init__.py')
            module_names = [
                'annotation.preannotators.' + f[:-3] for f in files
            ]
            cls.PREANNOTATOR_MODULES = [
                import_module(name) for name in module_names
            ]
        return cls.PREANNOTATOR_MODULES

    @classmethod
    def load_preannotators(cls, opts, header=None):
        return [getattr(module, clazz)(opts, header)
                for module in cls.get_preannotator_modules()
                for clazz in dir(module)
                if clazz.endswith('Preannotator')]

    @classmethod
    def load_preannotators_arguments(cls):
        result = {}
        for module in cls.get_preannotator_modules():
            result.update(getattr(module, 'get_arguments')())
        return result


def get_argument_parser():
    desc = "Program to annotate variants combining multiple annotating tools"
    parser = argparse.ArgumentParser(
        description=desc, conflict_handler='resolve')
    parser.add_argument(
        '-H', help='no header in the input file',
        default=False,  action='store_true', dest='no_header')
    parser.add_argument(
        '--config', help='config file location',
        required=True, action='store')
    parser.add_argument(
        '--append', help='always add columns; '
        'default behavior is to replace columns with the same label',
        default=False, action='store_true')
    # parser.add_argument(
    #     '--split', help='split variants based on given column',
    #     action='store')
    parser.add_argument(
        '--separator',
        help='separator used in the split column; defaults to ","',
        default='\t', action='store')
    parser.add_argument(
        '--options', help='add default arguments',
        dest='default_arguments', action='store', metavar=('=OPTION:VALUE'))
    # parser.add_argument(
    #     '--skip-preannotators', help='skips preannotators',
    #     action='store_true')
    parser.add_argument(
        '--read-parquet', help='read from a parquet file',
        action='store_true')
    parser.add_argument(
        '--write-parquet', help='write to a parquet file',
        action='store_true')

    for name, args in variant_format.get_arguments().items():
        parser.add_argument(name, **args)

    for name, args in PreannotatorLoader.\
            load_preannotators_arguments().items():
        parser.add_argument(name, **args)

    return parser


if __name__ == '__main__':
    main(get_argument_parser(), MultiAnnotator)
