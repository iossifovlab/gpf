#!/usr/bin/env python

import sys
import glob
import argparse
import ConfigParser
import common.config
import re
from os.path import exists, dirname, basename, realpath
from box import Box
from importlib import import_module
from ast import literal_eval
from collections import OrderedDict
from tools.utilities import assign_values
from tools.utilities import main as main
from tools import *


def str_to_class(val):
    return reduce(getattr, val.split("."), sys.modules[__name__])


class MyConfigParser(ConfigParser.SafeConfigParser):
    """Modified ConfigParser.SafeConfigParser that
    allows ':' in keys and only '=' as separator.
    """
    OPTCRE = re.compile(
        r'(?P<option>[^=\s][^=]*)'          # allow only =
        r'\s*(?P<vi>[=])\s*'                # for option separator
        r'(?P<value>.*)$'
        )


class MultiAnnotator(object):
    """
    `MultiAnnotator` class processes user passed options and annotates variant data.
    After processing of user options this class passes line by line the data
    to `Annotators` and `Preannotators`.

    Arguments of the constructor are:

    * `reannotate` - True/False. True - reannotate column and don't add new columns.
                     False - add new column and don't reannotate old columns.

    * `preannotators` - list of `Preannotators`

    * `split_column` - Column to split before annotation and generate values for
                       all parts of split column and after that to join new values
                       in one column.

    * `split_separator` - Separator for split column, default value is `,`
    """

    def __init__(self, opts, header=None):
        self.header = header
        self.preannotators = PreannotatorLoader.load_preannotators(opts, header)

        self.annotators = []
        virtual_columns_indices = []
        all_columns_labels = set()

        if not opts.skip_preannotators:
            for preannotator in self.preannotators:
                self.annotators.append({
                    'instance': preannotator,
                    'columns': OrderedDict([(c, c) for c in preannotator.new_columns])
                })
                all_columns_labels.update(preannotator.new_columns)
                if self.header:
                    self.header.extend(preannotator.new_columns)
                virtual_columns_indices.extend(
                    [assign_values(column, self.header)
                     for column in preannotator.new_columns])

        extracted_options = []
        if opts.default_arguments is not None:
            for option in opts.default_arguments:
                split_options = option.split(':')
                try:
                    split_options[1] = literal_eval(split_options[1])
                except ValueError:
                    pass
                extracted_options.append(split_options)
        default_arguments = dict(extracted_options)

        if opts.config is None:
            sys.stderr.write("You should provide a config file location.\n")
            sys.exit(-78)
        elif not exists(opts.config):
            sys.stderr.write("The provided config file does not exist!\n")
            sys.exit(-78)

        config_parser = MyConfigParser()
        config_parser.optionxform = str
        config_parser.read(opts.config)
        self.config = Box(common.config.to_dict(config_parser),
                          default_box=True, default_box_attr=None)

        # config_parser.sections() this gives the sections in order which is important
        for annotation_step in config_parser.sections():
            annotation_step_config = self.config[annotation_step]

            for default_argument, value in default_arguments.items():
                if annotation_step_config.options[default_argument] is None:
                    annotation_step_config.options[default_argument] = value

            step_columns_labels = annotation_step_config.columns.values()
            all_columns_labels.update(step_columns_labels)

            if self.header is not None:
                if opts.reannotate:
                    new_columns = [column for column in step_columns_labels
                                   if column not in self.header]
                else:
                    new_columns = step_columns_labels
                self.header.extend(new_columns)

            if annotation_step_config.virtuals is not None:
                virtual_columns_indices.extend(
                    [assign_values(annotation_step_config.columns[column.strip()], self.header)
                     for column in annotation_step_config.virtuals.split(',')])
            self.annotators.append({
                'instance': str_to_class(annotation_step_config.annotator)(
                    annotation_step_config.options, list(self.header)),
                'columns': annotation_step_config.columns
            })

        self.column_indices = {label: assign_values(label, self.header)
                               for label in all_columns_labels}
        self.stored_columns_indices = [i for i in range(1, len(self.header) + 1)
                                       if i not in virtual_columns_indices]

        if opts.split is None:
            self._split_variant = lambda v: [v]
            self._join_variant = lambda v: v[0]
        else:
            self.split_index = assign_values(opts.split, self.header)
            self.split_separator = opts.separator

    def _split_variant(self, line):
        return [line[:self.split_index-1] + [value] + line[self.split_index:]
                for value in line[self.split_index-1].split(self.split_separator)]

    def _join_variant(self, lines):
        return [column[0] if len(set(column)) == 1 else self.split_separator.join(column)
                for column in zip(*lines)]

    def annotate_file(self, file_io):
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
            file_io.line_write(self.header)

        annotators = self.annotators

        for line in file_io.lines_read():
            if '#' in line[0]:
                file_io.line_write(line)
                continue

            annotated = [annotate_line(segment)
                         for segment in self._split_variant(line)]
            annotated = self._join_variant(annotated)
            file_io.line_write([annotated[i-1] for i in self.stored_columns_indices])


class PreannotatorLoader(object):
    """
    Class for finding and loading `Preannotators`. It imports preannotator classes
    from `annotation/preannotators` and stores them in list.

    It is used by `MultiAnnotator`.
    """

    PREANNOTATOR_MODULES = None

    @classmethod
    def get_preannotator_modules(cls):
        if cls.PREANNOTATOR_MODULES is None:
            abs_files = glob.glob(dirname(realpath(__file__)) + '/preannotators/*.py')
            files = [basename(f) for f in abs_files]
            files.remove('__init__.py')
            module_names = ['preannotators.' + f[:-3] for f in files]
            cls.PREANNOTATOR_MODULES = [import_module(name) for name in module_names]
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
    desc = """Program to annotate variants combining multiple annotating tools"""
    parser = argparse.ArgumentParser(description=desc, conflict_handler='resolve')
    parser.add_argument('-H', help='no header in the input file',
                        default=False,  action='store_true', dest='no_header')
    parser.add_argument('-c', '--config', help='config file location',
                        required=True, action='store')
    parser.add_argument('--reannotate', help='always add columns; '
                        'default behavior is to replace columns with the same label',
                        default=False, action='store_true')
    parser.add_argument('--region', help='region to annotate (chr:begin-end) (input should be tabix indexed)',
                        action='store')
    parser.add_argument('--split', help='split variants based on given column',
                        action='store')
    parser.add_argument('--separator', help='separator used in the split column; defaults to ","',
                        default=',', action='store')
    parser.add_argument('--options', help='add default arguments',
                        dest='default_arguments', action='append', metavar=('=OPTION:VALUE'))
    parser.add_argument('--skip-preannotators', help='skips preannotators',
                        action='store_true')

    for name, args in PreannotatorLoader.load_preannotators_arguments().items():
        parser.add_argument(name, **args)

    return parser


if __name__ == '__main__':
    main(get_argument_parser(), MultiAnnotator)
