#!/usr/bin/env python

import sys
from os.path import exists, dirname, basename
import glob
import time, datetime
import argparse
import ConfigParser
import common.config
from box import Box
import pysam
from importlib import import_module
import gzip
from ast import literal_eval

from tools import *
from tools.utilities import assign_values
import preannotators.location

def str_to_class(val):
    return reduce(getattr, val.split("."), sys.modules[__name__])

class MultiAnnotator(object):

    def __init__(self, config_file, header=None, reannotate=False,
            preannotators=[], split_column=None, split_separator=',',
            default_arguments={}):
        self.header = header
        self.reannotate = reannotate
        self.preannotators = preannotators

        self.annotators = []
        virtual_columns_indices = []
        columns_labels = {}

        for preannotator in self.preannotators:
            self.annotators.append({
                'instance': preannotator,
                'columns': preannotator.new_columns
            })
            columns_labels.update({column: column
                                   for column in preannotator.new_columns})
            if self.header:
                self.header.extend(preannotator.new_columns)
            virtual_columns_indices.extend(
                [assign_values(column, self.header)
                 for column in preannotator.new_columns])

        config_parser = ConfigParser.SafeConfigParser()
        config_parser.optionxform = str
        config_parser.read(config_file)
        self.config = Box(common.config.to_dict(config_parser),
            default_box=True, default_box_attr=None)

        # config_parser.sections() this gives the sections in order which is important
        for annotation_step in config_parser.sections():
            annotation_step_config = self.config[annotation_step]

            for default_argument, value in default_arguments.items():
                if annotation_step_config.options[default_argument] is None:
                    annotation_step_config.options[default_argument] = value

            columns_labels.update(annotation_step_config.columns)
            if self.header is not None:
                if reannotate:
                    new_columns = [column
                                   for column in annotation_step_config.columns.values()
                                   if column not in self.header]
                else:
                    new_columns = annotation_step_config.columns.values()
                self.header.extend(new_columns)

            if annotation_step_config.virtuals is not None:
                virtual_columns_indices.extend(
                    [assign_values(annotation_step_config.columns[column.strip()], self.header)
                     for column in annotation_step_config.virtuals.split(',')])
            self.annotators.append({
                'instance': str_to_class(annotation_step_config.annotator)(
                    annotation_step_config.options, list(self.header)),
                'columns': annotation_step_config.columns.keys()
            })

        self.column_indices = {column: assign_values(label, self.header)
                               for column, label in columns_labels.items()}
        self.stored_columns_indices = [i for i in range(1, len(self.header) + 1)
                                       if i not in virtual_columns_indices]

        if split_column is None:
            self._split_variant = lambda v: [v]
            self._join_variant = lambda v: v[0]
        else:
            self.split_index = assign_values(split_column, self.header)
            self.split_separator = split_separator

    def _split_variant(self, line):
        return [line[:self.split_index-1] + [value] + line[self.split_index:]
                for value in line[self.split_index-1].split(self.split_separator)]

    def _join_variant(self, lines):
        return [column[0] if len(set(column)) == 1 else self.split_separator.join(column)
                for column in zip(*lines)]

    def annotate_file(self, input, output):
        if self.header:
            output.write("#")
            output.write("\t".join([self.header[i-1]
                                    for i in self.stored_columns_indices]))
            output.write("\n")

        sys.stderr.write("...processing....................\n")

        annotators = self.annotators
        def annotate_line(line):
            for annotator in annotators:
                columns = annotator['columns']
                values = annotator['instance'].line_annotations(line, columns)
                for column, value in zip(columns, values):
                    position = self.column_indices[column]
                    line[position - 1:position] = [value]
            return line

        k = 0
        for l in input:
            if l[0] == "#":
                output.write(l)
                continue
            k += 1
            if k%1000 == 0:
                sys.stderr.write(str(k) + " lines processed\n")

            line = self._join_variant(
                [annotate_line(line)
                 for line in self._split_variant(l.rstrip('\n').split("\t"))])


            line = [line[i-1] for i in self.stored_columns_indices]

            output.write("\t".join(line) + "\n")


class PreannotatorLoader(object):

    PREANNOTATOR_MODULES = None

    @classmethod
    def get_preannotator_modules(cls):
        if cls.PREANNOTATOR_MODULES is None:
            abs_files = glob.glob(dirname(__file__) + '/preannotators/*.py')
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
    parser.add_argument('-H', help='no header in the input file', default=False,  action='store_true', dest='no_header')
    parser.add_argument('-c', '--config', help='config file location', required=True, action='store')
    parser.add_argument('--always-add', help='always add columns; '
                        'default behavior is to replace columns with the same label',
                        default=False, action='store_true')
    parser.add_argument('--region', help='region to annotate (chr:begin-end) (input should be tabix indexed)', action='store')
    parser.add_argument('--split', help='split variants based on given column', action='store')
    parser.add_argument('--separator', help='separator used in the split column; defaults to ","',
        default=',', action='store')
    parser.add_argument('--options', help='add default arguments', action='append', metavar=('=OPTION:VALUE'))
    parser.add_argument('infile', nargs='?', action='store',
        default='-', help='path to input file; defaults to stdin')
    parser.add_argument('outfile', nargs='?', action='store',
        default='-', help='path to output file; defaults to stdout')
    
    for name, args in PreannotatorLoader.load_preannotators_arguments().items():
        parser.add_argument(name, **args)

    return parser


def main():
    start=time.time()

    opts = get_argument_parser().parse_args()

    if not opts.config:
        sys.stderr.write("You should provide a config file location.\n")
        sys.exit(-78)
    elif not exists(opts.config):
        sys.stderr.write("The provided config file does not exist!\n")
        sys.exit(-78)

    if opts.infile != '-' and exists(opts.infile) == False:
        sys.stderr.write("The given input file does not exist!\n")
        sys.exit(-78)

    if opts.infile == '-':
        variantFile = sys.stdin
    elif opts.region:
        tabix_file = pysam.TabixFile(opts.infile)
        variantFile = tabix_file.fetch(region=opts.region)
    else:
        variantFile = open(opts.infile)

    if opts.no_header == False:
        if opts.region is None:
            header_str = variantFile.readline()[:-1]
        else:
            with gzip.open(opts.infile) as file:
                header_str = file.readline()[:-1]
        if header_str[0] == '#':
            header_str = header_str[1:]
        header = header_str.split('\t')
    else:
        header = None

    if opts.outfile != '-':
        out = open(opts.outfile, 'w')
    else:
        out = sys.stdout

    options = []
    if opts.options is not None:
        for option in opts.options:
            split_options = option.split(':')

            try:
                split_options[1] = literal_eval(split_options[1])
            except ValueError:
                pass

            options.append(split_options)

    preannotators = PreannotatorLoader.load_preannotators(opts, header)

    annotator = MultiAnnotator(opts.config, header, not opts.always_add,
        preannotators, opts.split, opts.separator, dict(options))

    annotator.annotate_file(variantFile, out)

    if opts.infile != '-' and not opts.region:
        variantFile.close()

    if opts.outfile != '-':
        out.close()
        sys.stderr.write("Output file saved as: " + opts.outfile + "\n")

    sys.stderr.write("The program was running for [h:m:s]: " + str(datetime.timedelta(seconds=round(time.time()-start,0))) + "\n")


if __name__ == '__main__':
    main()
