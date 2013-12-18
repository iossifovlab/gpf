#!/bin/env python

import argparse
import itertools
import sys

from query_variants import do_query_variants, join_line


parser = argparse.ArgumentParser(description="Query denovo and inheritted variants.")
parser.add_argument('--denovoStudies', type=str, 
        default="allPublishedWEWithOurCallsAndTG",
        help='the studies to query for denovo variants. (i.e. None; allPublishedPlusOurRecent; all; allPublished; wig683; IossifovWE2012; DalyWE2012; StateWE2012; EichlerWE2012); type "--denovoStudies None" to get transmitted variants only')
parser.add_argument('--transmittedStudy', type=str, default="wig683",
        help='the study to query the transmitted variants (type "--transmittedStudy None" to get de novo variants only)')
parser.add_argument('--effectTypes', type=str, default="LGDs", 
        help='effect types (i.e. LGDs,missense,synonymous,frame-shift). LGDs by default. none for all variants')
parser.add_argument('--variantTypes', type=str, 
        help='variant types (i.e. sub or ins,del)')
parser.add_argument('--popFrequencyMax', type=str, default="1.0",
        help='maximum population frequency in percents. Can be 100 or -1 for no limit; ultraRare. 1.0 by default.')
parser.add_argument('--popFrequencyMin', type=str, default="-1",
        help='minimum population frequency in percents. Can be -1 for no limit. -1 by default.')
parser.add_argument('--popMinParentsCalled', type=str, default="600",
        help='minimum number of genotyped parents. Can be -1 for no limit. 600 by default.')
parser.add_argument('--inChild', type=str, 
        help='i.e. prb, sib, prbM, sibF')
parser.add_argument('--familiesFile', type=str, 
        help='a file with a list of the families to report')
parser.add_argument('--familiesList', type=str, 
        help='comma separated llist of the familyIds')
parser.add_argument('--geneSet', type=str, help='gene set id of the form "collection:setid"')
parser.add_argument('--geneSym', type=str, help='list of gene syms')
parser.add_argument('--geneSymFile', type=str, help='the first column should cotain gene symbols')
parser.add_argument('--geneId', type=str, help='list of gene ids')
parser.add_argument('--geneIdFile', type=str, help='the first column should cotain gene ids')
parser.add_argument('--regionS', type=str, help='region')
args = parser.parse_args()

print >>sys.stderr, args

args_dict = {a: getattr(args, a) for a in dir(args) if a[0] != '_'}
print >>sys.stderr, args_dict

generator = do_query_variants(args_dict)

for v in generator:
    sys.stdout.write(join_line(v, '\t'))
