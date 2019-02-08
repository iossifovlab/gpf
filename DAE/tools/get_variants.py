#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
import argparse
import sys

from query_variants import do_query_variants, join_line
from query_prepare import prepare_gene_syms
from DAE import get_gene_sets_symNS


def get_variants(args_dict):
    gene_syms = combine_gene_syms(args_dict)
    args_dict['geneSyms'] = list(gene_syms) if gene_syms else None
    if 'geneSet' in args_dict:
        del args_dict['geneSet']
    if 'geneTerm' in args_dict:
        del args_dict['geneTerm']
    generator = do_query_variants(args_dict)
    return generator


def parse_cli_arguments(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Query denovo and inheritted variants.")

    parser.add_argument(
        '--denovoStudies', type=str,
        default="allPublishedWEWithOurCallsAndTG",
        help='''the studies to query for denovo variants. (i.e. None;
        allPublishedPlusOurRecent; all; allPublished; wig683; IossifovWE2012;
        DalyWE2012; StateWE2012; EichlerWE2012); type "--denovoStudies None"
        to get transmitted variants only''')

    parser.add_argument(
        '--transmittedStudy', type=str, default="None",
        help='''the study to query the transmitted variants
(type "--transmittedStudy None" to get de novo variants only)''')

    parser.add_argument(
        '--effectTypes', type=str, default="LGDs",
        help='''effect types (i.e. LGDs,missense,synonymous,frame-shift).
LGDs by default. none for all variants''')

    parser.add_argument(
        '--variantTypes', type=str,
        help='variant types (i.e. sub or ins,del)')
    parser.add_argument(
        '--popFrequencyMax', type=str, default="1.0",
        help='''maximum population frequency in percents.
        Can be 100 or -1 for no limit; ultraRare. 1.0 by default.''')
    parser.add_argument(
        '--popFrequencyMin', type=str, default="-1",
        help='''minimum population frequency in percents. Can be -1 for no limit.
        -1 by default.''')
    parser.add_argument(
        '--popMinParentsCalled', type=str, default="0",
        help='''minimum number of genotyped parents. Can be -1 for no limit.
        0 by default.''')
    parser.add_argument(
        '--TMM_ALL',
        help='Speeds up global transmitted data queries',
        action="store_true")
    parser.add_argument(
        '--inChild', type=str,
        help='i.e. prb, sib, prbM, sibF')
    parser.add_argument(
        '--familiesFile', type=str,
        help='a file with a list of the families to report')
    parser.add_argument(
        '--familiesList', type=str,
        help='comma separated llist of the familyIds')
    parser.add_argument(
        '--geneSet', type=str,
        help='gene set id of the form "collection:setid"')
    parser.add_argument(
        '--geneSym', type=str,
        help='list of gene syms')
    parser.add_argument(
        '--geneSymFile', type=str,
        help='the first column should cotain gene symbols')
    parser.add_argument(
        '--geneId', type=str,
        help='list of gene ids')
    parser.add_argument(
        '--geneIdFile', type=str,
        help='the first column should cotain gene ids')
    parser.add_argument('--regionS', type=str, help='region')

    parser.add_argument(
        '--familyRace', type=str,
        help='''family race; one of 'african-amer', 'asian',
        'more-than-one-race',
        'native-american', 'native-hawaiian', 'white' ''')
    parser.add_argument(
        '--familyVerbalIqLo', type=int,
        help='proband verbal IQ low limit')
    parser.add_argument(
        '--familyVerbalIqHi', type=int,
        help='proband verbal IQ high limit')
    parser.add_argument(
        '--familyQuadTrio', type=str,
        help='filter Quad or Trio families; should be one of "Quad" or "Trio"')
    parser.add_argument(
        '--familyPrbGender', type=str,
        help='gender of the proband ("male" or "female")')
    parser.add_argument(
        '--familySibGender', type=str,
        help='gender of the sibling ("male" or "female")')

    args = parser.parse_args(argv)

    print(args, file=sys.stderr)

    args_dict = {a: getattr(args, a) for a in dir(args) if a[0] != '_'}

    if 'geneSet' in args_dict and args_dict['geneSet']:
        gene_set, gene_term = args_dict['geneSet'].split(':')
        args_dict['geneSet'] = gene_set
        args_dict['geneTerm'] = gene_term
        gs = prepare_gene_sets(args_dict)
        if not gs:
            raise ValueError("wrong gene set: {}:{}".format(gene_set,
                                                            gene_term))

    print(args_dict, file=sys.stderr)
    return args_dict


def prepare_gene_sets(data):
    if 'geneSet' not in data or not data['geneSet'] \
            or not data['geneSet'].strip():
        return None

    if 'geneTerm' not in data or not data['geneTerm'] \
            or not data['geneTerm'].strip():
        return None

    gene_set = data['geneSet']
    gene_term = data['geneTerm']

    gt = get_gene_sets_symNS(gene_set)
    if gt and gene_term in gt.t2G:
            return set(gt.t2G[gene_term].keys())

    return None


def combine_gene_syms(data):
    gene_syms = prepare_gene_syms(data)
    gene_sets = prepare_gene_sets(data)

    if gene_syms is None:
        return gene_sets
    else:
        if gene_sets is None:
            return gene_syms
        else:
            return gene_sets.union(gene_syms)


if __name__ == "__main__":

    print(sys.argv, file=sys.stderr)
    try:
        args_dict = parse_cli_arguments(sys.argv[1:])
        generator = get_variants(args_dict)

        for l in generator:
            sys.stdout.write(join_line(l, '\t'))
    except ValueError as ex:
        print("ERROR:", ex, file=sys.stderr)
        sys.exit(1)
