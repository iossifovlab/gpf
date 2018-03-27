#!/usr/bin/env python

import os, sys
import time, datetime
import optparse
import ConfigParser
import common.config
from box import Box
import pysam

from annotate_variants import EffectAnnotator
from add_missense_scores import MissenseScoresAnnotator
from annotate_with_genomic_scores import GenomicScoresAnnotator

def str_to_class(val):
    return reduce(getattr, val.split("."), sys.modules[__name__])

class MultiAnnotator(object):

    def __init__(self, config_file, header=None, reannotate=False):
        self.header = header
        self.reannotate = reannotate
        config_parser = ConfigParser.SafeConfigParser()
        config_parser.optionxform = str
        config_parser.read(config_file)
        self.config = Box(common.config.to_dict(config_parser),
            default_box=True, default_box_attr=None)

        self.annotators = []
        new_columns_labels = []
        columns_labels = {}
        # config_parser.sections() this gives the sections in order which is important
        for annotation_step in config_parser.sections():
            annotation_step_config = self.config[annotation_step]
            columns_labels.update(annotation_step_config.columns)
            if not reannotate and self.header is not None:
                self.header.extend(annotation_step_config.columns.values())
            self.annotators.append({
                'instance': str_to_class(annotation_step_config.annotator)(
                    annotation_step_config.options, self.header),
                'columns': annotation_step_config.columns.keys()
            })

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
            output.write("\t".join(self.header) + "\n")

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

            line = l.split("\t")
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

            output.write("\t".join(line) + "\n")


def get_argument_parser():
    desc = """Program to annotate variants combining multiple annotating tools"""
    parser = optparse.OptionParser(description=desc, add_help_option=False)
    parser.add_option('-h', '--help', default=False, action='store_true')
    parser.add_option('-H', help='no header in the input file', default=False,  action='store_true', dest='no_header')
    parser.add_option('-c', '--config', help='config file location', action='store')
    parser.add_option('--reannotate', help='columns in the input file to reannotate', action='store')
    parser.add_option('--region', help='region to annotate (chr:begin-end)', action='store')
    return parser


def print_help():
    print("\n\n----------------------------------------------------------------\n\nProgram to combine annotation tools for genomic variants")
    print("BASIC USAGE: annotate_variant.py <INFILE> <OUTFILE> <options>\n")
    print("-h, --help                       show this help message and exit")
    print("-H                               no header in the input file ")
    print("-c, --config                     config file location")
    print("--reannotate                     columns in the input file to reannotate")
    print("\nConfig file format:\n")
    print("[annotation]")
    print("steps=<annotation step>[,<annotation step>]*")
    print("steps.<annotation step>.args=<arguments to pass to <annotation step>>")
    print("steps.<annotation step>.columns=<output column key>:<column label>[,<output column key>:<column label>]*")


def main():
    start=time.time()

    (opts, args) = get_argument_parser().parse_args()

    if opts.help:
        print_help()
        sys.exit(0)

    infile = '-'
    outfile = None

    if not opts.config:
        sys.stderr.write("You should provide a config file location.\n")
        sys.exit(-78)
    elif not os.path.exists(opts.config):
        sys.stderr.write("The provided config file does not exist!\n")
        sys.exit(-78)

    if len(args) > 0:
        infile = args[0]

    if infile != '-' and os.path.exists(infile) == False:
        sys.stderr.write("The given input file does not exist!\n")
        sys.exit(-78)

    if len(args) > 1:
        outfile = args[1]
    if outfile=='-':
        outfile = None

    if infile=='-':
        variantFile = sys.stdin
    else:
        variantFile = pysam.TabixFile(infile)

    if opts.no_header == False:
        if infile == '-':
            header_str = variantFile.readline()[:-1]
        else:
            header_str = variantFile.header.next()
        header = header_str[1:].split('\t')
    else:
        header = None

    if outfile != None:
        out = open(outfile, 'w')
    else:
        out = sys.stdout

    if opts.reannotate:
        opts.reannotate = {token.strip() for token in opts.reannotate.split(',')}

    annotator = MultiAnnotator(opts.config, header, opts.reannotate)

    annotator.annotate_file(variantFile.fetch(region=opts.region), out)

    if infile != '-':
        variantFile.close()

    if outfile != None:
        out.close()
        sys.stderr.write("Output file saved as: " + outfile + "\n")

    sys.stderr.write("The program was running for [h:m:s]: " + str(datetime.timedelta(seconds=round(time.time()-start,0))) + "\n")


if __name__ == '__main__':
    main()
