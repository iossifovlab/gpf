#!/usr/bin/env python

from __future__ import absolute_import
from builtins import str
from builtins import range
from builtins import object
import sys
from os.path import exists, dirname, basename
import glob
import time, datetime
import argparse
from future import standard_library
standard_library.install_aliases()
from configparser import ConfigParser
import common.config
from box import Box
import pysam
from importlib import import_module

from .tools import *
from .tools.utilities import assign_values
from .preannotators import location
from functools import reduce

def str_to_class(val):
    return reduce(getattr, val.split("."), sys.modules[__name__])

class MultiAnnotator(object):

    def __init__(self, config_file, header=None, reannotate=False, preannotators=[]):
        self.header = header
        self.reannotate = reannotate
        self.preannotators = preannotators

        self.annotators = []
        virtual_columns_indices = []

        for preannotator in self.preannotators:
            self.annotators.append({
                'instance': preannotator,
                'columns': preannotator.new_columns
            })
            self.header.extend(preannotator.new_columns)
            virtual_columns_indices.extend(
                [assign_values(column, self.header)
                 for column in preannotator.new_columns])

        config_parser = ConfigParser()
        config_parser.optionxform = str
        config_parser.read(config_file)
        self.config = Box(common.config.to_dict(config_parser),
            default_box=True, default_box_attr=None)

        new_columns_labels = []
        columns_labels = {}
        # config_parser.sections() this gives the sections in order which is important
        for annotation_step in config_parser.sections():
            annotation_step_config = self.config[annotation_step]
            columns_labels.update(annotation_step_config.columns)
            if not reannotate and self.header is not None:
                self.header.extend(list(annotation_step_config.columns.values()))
            if annotation_step_config.virtuals is not None:
                virtual_columns_indices.extend(
                    [assign_values(annotation_step_config.columns[column.strip()], self.header)
                     for column in annotation_step_config.virtuals.split(',')])
            self.annotators.append({
                'instance': str_to_class(annotation_step_config.annotator)(
                    annotation_step_config.options, list(self.header)),
                'columns': list(annotation_step_config.columns.keys())
            })

        self.stored_columns_indices = [i for i in range(1, len(self.header) + 1)
                                       if i not in virtual_columns_indices]

        if reannotate:
            reannotate_labels = {columns_labels[column] for column in reannotate}
            if not reannotate_labels.issubset(self.header):
                raise ValueError('All reannotate columns should be present in the input file header!')
            self.reannotate_indices = {
                column: self.header.index(columns_labels[column])
                for column in reannotate
            }


    def annotate_file(self, input, output):
        if self.header:
            output.write("#")
            output.write("\t".join([self.header[i-1]
                                    for i in self.stored_columns_indices]))
            output.write("\n")

        sys.stderr.write("...processing....................\n")
        k = 0
        annotators = self.annotators
        for l in input:
            if l[0] == "#":
                output.write(l)
                continue
            k += 1
            if k%1000 == 0:
                sys.stderr.write(str(k) + " lines processed\n")

            line = l.rstrip('\n').split("\t")
            if self.reannotate:
                for annotator in annotators:
                    columns_to_update = [column
                        for column in annotator['columns']
                        if column in self.reannotate]
                    values = annotator['instance'].line_annotations(line, columns_to_update)
                    for index in range(0, len(columns_to_update)):
                        position = self.reannotate_indices[columns_to_update[index]]
                        line[position] = values[index]
            else:
                for annotator in annotators:
                    line.extend(annotator['instance'].line_annotations(line, annotator['columns']))
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
    parser.add_argument('--reannotate', help='columns in the input file to reannotate', action='store')
    parser.add_argument('--region', help='region to annotate (chr:begin-end) (input should be tabix indexed)', action='store')
    parser.add_argument('infile', nargs='?', action='store',
        default='-', help='path to input file; defaults to stdin')
    parser.add_argument('outfile', nargs='?', action='store',
        default='-', help='path to output file; defaults to stdout')
    
    for name, args in list(PreannotatorLoader.load_preannotators_arguments().items()):
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
            header_str = list(tabix_file.header)[0]
        if header_str[0] == '#':
            header_str = header_str[1:]
        header = header_str.split('\t')
    else:
        header = None

    if opts.outfile != '-':
        out = open(opts.outfile, 'w')
    else:
        out = sys.stdout

    if opts.reannotate:
        opts.reannotate = {token.strip() for token in opts.reannotate.split(',')}

    preannotators = PreannotatorLoader.load_preannotators(opts, header)

    annotator = MultiAnnotator(opts.config, header, opts.reannotate, preannotators)

    annotator.annotate_file(variantFile, out)

    if opts.infile != '-' and not opts.region:
        variantFile.close()

    if opts.outfile != '-':
        out.close()
        sys.stderr.write("Output file saved as: " + opts.outfile + "\n")

    sys.stderr.write("The program was running for [h:m:s]: " + str(datetime.timedelta(seconds=round(time.time()-start,0))) + "\n")


if __name__ == '__main__':
    main()
