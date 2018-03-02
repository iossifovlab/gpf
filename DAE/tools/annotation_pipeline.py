#!/usr/bin/env python

import os, sys
import time, datetime
import optparse
import ConfigParser

from annotate_variants import EffectAnnotator

''' config
[annotation]

steps=effects,missense scores
steps.effects.args=-c chr -p position -v variant
steps.effects.columns=effect_type:effect type,...

'''

class MultiAnnotator(object):

    ANNOTATOR_CLASSES = {
        'effects': EffectAnnotator
    }

    def __init__(self, config_file, header):
        self.header = header
        self.config = ConfigParser.SafeConfigParser()
        self.config.read(config_file)

        annotation_steps = [step.strip()
                 for step in self.config.get('annotation', 'steps').split(',')]

        self.annotators = []
        new_columns_labels = []
        for annotation_step in annotation_steps:
            args = self.config.get('annotation', 'steps.{}.args'.format(annotation_step))
            columns_str = self.config.get('annotation', 'steps.{}.columns'.format(annotation_step))
            columns = [tuple([token.strip() for token in column.split(':')])
                       for column in columns_str.split(',')]
            self.annotators.append({
                'instance': self.ANNOTATOR_CLASSES[annotation_step](
                    args=args.split(' '), header=header),
                'columns': [column[0] for column in columns]
            })
            new_columns_labels.extend([column[1] for column in columns])

        if header is not None:
            self.header += new_columns_labels

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

            line = l[:-1].split("\t")
            for annotator in annotators:
                line.extend(annotator['instance'].line_annotations(line, annotator['columns']))

            output.write("\t".join(line) + "\n")


def get_argument_parser():
    desc = """Program to annotate variants combining multiple annotating tools"""
    parser = optparse.OptionParser(description=desc, add_help_option=False)
    parser.add_option('-h', '--help', default=False, action='store_true')
    parser.add_option('-H', help='no header in the input file', default=False,  action='store_true', dest='no_header')
    parser.add_option('-c', '--config', help='config file location', action='store')
    return parser


def print_help():
    print("\n\n----------------------------------------------------------------\n\nProgram to combine annotation tools for genomic variants")
    print("BASIC USAGE: annotate_variant.py <INFILE> <OUTFILE> <options>\n")
    print("-h, --help                       show this help message and exit")
    print("-H                               no header in the input file ")
    print("-c, --config                     config file location")
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
        variantFile = open(infile)

    if opts.no_header == False:
        header_str = variantFile.readline()
        header = header_str.split()
    else:
        header = None

    if outfile != None:
        out = open(outfile, 'w')
    else:
        out = sys.stdout

    annotator = MultiAnnotator(opts.config, header)
    annotator.annotate_file(variantFile, out)

    if infile != '-':
        variantFile.close()

    if outfile != None:
        out.close()
        sys.stderr.write("Output file saved as: " + outfile + "\n")

    sys.stderr.write("The program was running for [h:m:s]: " + str(datetime.timedelta(seconds=round(time.time()-start,0))) + "\n")


if __name__ == '__main__':
    main()