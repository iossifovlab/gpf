#!/usr/bin/env python

# Oct 9th 2013
# written by Ewa

import argparse
import re, os.path, sys
import GenomeAccess
from GeneModelFiles import load_gene_models
from variant_annotation.annotator import VariantAnnotator as VariantAnnotation
from utilities import *

class ColumnOrderAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        if not hasattr(namespace, 'order'):
            namespace.order = []
        namespace.order.append(self.dest)

def get_argument_parser():
    """
    EffectAnnotator options::

        usage: annotate_variants.py [-h] [-c C] [-p P] [-x X] [-v V] [-a A] [-r R]
                            [-t T] [-q Q] [-l L] [-P PROM_LEN] [-H] [-T T]
                            [--Traw TRAW] [--TrawFormat TRAWFORMAT] [-G G]
                            [--Graw GRAW] [-I I] [--effect-type EFFECT_TYPE]
                            [--effect-gene EFFECT_GENE]
                            [--effect-details EFFECT_DETAILS]
                            [infile] [outfile]

        Program to annotate variants (substitutions & indels & cnvs)

        positional arguments:
          infile                path to input file; defaults to stdin
          outfile               path to output file; defaults to stdout

        optional arguments:
          -h, --help            show this help message and exit
          -c C                  chromosome column number/name
          -p P                  position column number/name
          -x X                  location (chr:pos) column number/name
          -v V                  variant column number/name
          -a A                  alternative allele (FOR SUBSTITUTIONS ONLY) column
                                number/name
          -r R                  reference allele (FOR SUBSTITUTIONS ONLY) column
                                number/name
          -t T                  type of mutation column number/name
          -q Q                  seq column number/name
          -l L                  length column number/name
          -P PROM_LEN           promoter length
          -H                    no header in the input file
          -T T                  gene models ID <RefSeq, CCDS, knownGene>
          --Traw TRAW           outside gene models file path
          --TrawFormat TRAWFORMAT
                                outside gene models format (refseq, ccds, knowngene)
          -G G                  genome ID <GATK_ResourceBundle_5777_b37_phiX174, hg19>
          --Graw GRAW           outside genome file
          -I I                  geneIDs mapping file; use None for no gene name
                                mapping
          --effect-type EFFECT_TYPE
                                name to use for effect type column
          --effect-gene EFFECT_GENE
                                name to use for effect gene column
          --effect-details EFFECT_DETAILS
                                name to use for effect details column

    """
    desc = """Program to annotate variants (substitutions & indels & cnvs)"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-c', help='chromosome column number/name', action='store')
    parser.add_argument('-p', help='position column number/name', action='store')
    parser.add_argument('-x', help='location (chr:pos) column number/name', action='store')
    parser.add_argument('-v', help='variant column number/name', action='store')
    parser.add_argument('-a', help='alternative allele (FOR SUBSTITUTIONS ONLY) column number/name', action='store')
    parser.add_argument('-r', help='reference allele (FOR SUBSTITUTIONS ONLY) column number/name', action='store')
    parser.add_argument('-t', help='type of mutation column number/name', action='store')
    parser.add_argument('-q', help='seq column number/name', action='store')
    parser.add_argument('-l', help ='length column number/name', action='store')

    parser.add_argument('-P', help='promoter length', default=0, action='store', type=int, dest = "prom_len")
    parser.add_argument('-H',help='no header in the input file', default=False,  action='store_true', dest='no_header')

    parser.add_argument('-T', help='gene models ID <RefSeq, CCDS, knownGene>', type=str, action='store')
    parser.add_argument('--Traw', help='outside gene models file path', type=str, action='store')
    parser.add_argument('--TrawFormat', help='outside gene models format (refseq, ccds, knowngene)', type=str, action='store')

    parser.add_argument('-G', help='genome ID <GATK_ResourceBundle_5777_b37_phiX174, hg19> ', type=str, action='store')
    parser.add_argument('--Graw', help='outside genome file', type=str, action='store')

    parser.add_argument('-I', help='geneIDs mapping file; use None for no gene name mapping', default="default", type=str, action='store')

    parser.add_argument('--effect-type', help='name to use for effect type column', type=str, action=ColumnOrderAction)
    parser.add_argument('--effect-gene', help='name to use for effect gene column', type=str, action=ColumnOrderAction)
    parser.add_argument('--effect-details', help='name to use for effect details column', type=str, action=ColumnOrderAction)

    return parser


class EffectAnnotator(AnnotatorBase):

    def __init__(self, opts, header=None):
        super(EffectAnnotator, self).__init__(opts, header)
        self._init_cols()
        self._init_variant_annotation()

    def _init_cols(self):
        opts = self.opts
        header = self.header

        if opts.x == None and opts.c == None:
            opts.x = "location"
        if (opts.v == None and opts.a == None) and (opts.v == None and opts.t == None):
            opts.v = "variant"

        self.chrCol = assign_values(opts.c, header)
        self.posCol = assign_values(opts.p, header)
        self.locCol = assign_values(opts.x, header)
        self.varCol = assign_values(opts.v, header)
        self.altCol = assign_values(opts.a, header)
        self.refCol = assign_values(opts.r, header)
        self.typeCol = assign_values(opts.t, header)
        self.seqCol = assign_values(opts.q, header)
        self.lengthCol = assign_values(opts.l, header)

        self.argColumnNs = [self.chrCol, self.posCol, self.locCol, self.varCol,
            self.refCol, self.altCol, self.lengthCol, self.seqCol, self.typeCol]

        if hasattr(opts, 'order') and opts.order is not None:
            new_col_labels = [getattr(opts, col) for col in opts.order]
        else:
            opts.order = ['effect_type', 'effect_gene', 'effect_details']
            new_col_labels = ['effectType', 'effectGene', 'effectDetails']
        self.header = header + new_col_labels

    def _init_variant_annotation(self):
        opts = self.opts
        if opts.I == "None":
            opts.I = None

        if opts.Graw == None:
            from DAE import genomesDB

        if opts.G == None and opts.Graw == None:
            GA = genomesDB.get_genome()
            if opts.T == None and opts.Traw == None:
                gmDB = genomesDB.get_gene_models()
            elif opts.Traw == None:
                gmDB = genomesDB.get_gene_models(opts.T)
            else:
                gmDB = load_gene_models(opts.Traw, opts.I, opts.TrawFormat)

        elif opts.Graw == None:
            GA = genomesDB.get_genome(opts.G)
            if opts.T == None and opts.Traw == None:
                gmDB = genomesDB.get_gene_models(genome=opts.G)
            elif opts.Traw == None:
                gmDB = genomesDB.get_gene_models(opts.T, genome=opts.G)
            else:
                gmDB = load_gene_models(opts.Traw, opts.I, opts.TrawFormat)

        else:
            GA = GenomeAccess.openRef(opts.Graw)
            if opts.Traw == None:
                sys.stderr.write("This genome requires gene models (--Traw option)\n")
                sys.exit(-783)
            gmDB = load_gene_models(opts.Traw, opts.I, opts.TrawFormat)


        if "1" in GA.allChromosomes and "1" not in gmDB._utrModels.keys():
            gmDB.relabel_chromosomes()

        sys.stderr.write("GENOME: " + GA.genomicFile + "\n")
        sys.stderr.write("GENE MODEL FILES: " + gmDB.location + "\n")
        if opts.prom_len is None:
            opts.prom_len = 0
        self.annotation_helper = VariantAnnotation(GA, gmDB, promoter_len=opts.prom_len)

    @property
    def new_columns(self):
        return self.opts.order

    def line_annotations(self, line, new_cols_order):
        params = [line[i-1] if i!=None else None for i in self.argColumnNs]

        try:
            effects = self.annotation_helper.do_annotate_variant(*params)
            effect_type, effect_gene, effect_details = self.annotation_helper.effect_description(effects)
            return [locals()[col] for col in new_cols_order]
        except ValueError as e:
            return ['' for col in new_cols_order]



if __name__ == "__main__":
    main(get_argument_parser(), EffectAnnotator)
