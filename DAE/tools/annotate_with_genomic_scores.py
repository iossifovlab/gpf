#!/bin/env python

# Dec 12th 2013
# by Ewa

from GenomicScores import load_genomic_scores
from utilities import *
import optparse

def get_argument_parser():
    desc = """Program to annotate genomic positions with genomic scores (GERP, PhyloP, phastCons, nt, GC, cov)"""
    parser = optparse.OptionParser(version='%prog version 1.0 12/December/2013', description=desc, add_help_option=False)
    parser.add_option('-h', '--help', default=False, action='store_true')
    parser.add_option('-c', help='chromosome column number/name', action='store')
    parser.add_option('--chr-format', help='chromosome format [hg19|GATK]', action='store')
    parser.add_option('-p', help='position column number/name', action='store')
    parser.add_option('-x', help='location (chr:pos) column number/name', action='store')
    parser.add_option('-F', help='genomic score file', action='store')
    parser.add_option('-S', help='scores subset [string - colon separated]', action='store')
    parser.add_option('-H',help='no header in the input file', default=False,  action='store_true', dest='no_header')
    return parser

class GenomicScoresAnnotator(object):

    def __init__(self, opts, header=None):
        self.opts = opts
        self.header = header

        if opts.x == None and opts.c == None:
            opts.x = "location"

        self.chrCol = assign_values(opts.c, header)
        self.posCol = assign_values(opts.p, header)
        self.locCol = assign_values(opts.x, header)

        self.genomic_scores = load_genomic_scores(opts.F)
        if opts.chr_format is None:
            opts.chr_format = "GATK"

        if self.genomic_scores.chr_format != opts.chr_format:
            if self.genomic_scores.chr_format == "hg19":
                self.genomic_scores.relabel_chromosomes()
            else:
                self.genomic_scores.relabel_chromosomes(gatk=False, hg19=True)

        if opts.S is not None:
            self.scores = opts.S.split(";")
        else:
            self.scores = self.genomic_scores._score_names

    def annotate_file(self, input, output):
        if self.opts.no_header == False:
            output.write("\t".join(self.header + self.scores) + "\n")
        sys.stderr.write("...processing....................\n")

        for l in input:
            if l[0] == "#":
               output.write(l)
               continue
            line = l[:-1].split("\t")
            line_scores = self.line_annotations(line, self.scores)
            output.write("\t".join(line + line_scores) + "\n")

    def line_annotations(self, line, scores_in_order):
        if self.locCol != None:
            location = line[self.locCol]
        else:
            location = line[self.chrCol] + ":" + line[self.posCol]

        line_scores = map(str,
            self.genomic_scores.get_score(location, scores_in_order))
        if not line_scores:
            line_scores = ['NA'] * len(self.scores)
        return line_scores


if __name__ == '__main__':
    main(get_argument_parser(), GenomicScoresAnnotator)
