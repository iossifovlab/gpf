#!/bin/env python

# Dec 12th 2013
# by Ewa

from __future__ import absolute_import
from GenomicScores import load_genomic_scores
from .utilities import *
import argparse

def get_argument_parser():
    desc = """Program to annotate genomic positions with genomic scores (GERP, PhyloP, phastCons, nt, GC, cov)"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-c', help='chromosome column number/name', action='store')
    parser.add_argument('--chr-format', help='chromosome format [hg19|GATK]', action='store')
    parser.add_argument('-p', help='position column number/name', action='store')
    parser.add_argument('-x', help='location (chr:pos) column number/name', action='store')
    parser.add_argument('-F', help='genomic score file', action='store')
    parser.add_argument('-S', help='scores subset [string - colon separated]', action='store')
    parser.add_argument('-H',help='no header in the input file', default=False,  action='store_true', dest='no_header')
    return parser

class GenomicScoresAnnotator(AnnotatorBase):

    def __init__(self, opts, header=None):
        super(GenomicScoresAnnotator, self).__init__(opts, header)

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
        self.header = self.header + self.scores

    @property
    def new_columns(self):
        return self.scores

    def line_annotations(self, line, scores_in_order):
        if self.locCol != None:
            location = line[self.locCol]
        else:
            location = line[self.chrCol] + ":" + line[self.posCol]

        line_scores = map(str,
            self.genomic_scores.get_score(location, scores_in_order))
        if not line_scores:
            line_scores = ['NA'] * len(scores_in_order)
        return line_scores


if __name__ == '__main__':
    main(get_argument_parser(), GenomicScoresAnnotator)
