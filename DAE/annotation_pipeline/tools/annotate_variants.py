#!/usr/bin/env python

# Oct 9th 2013
# written by Ewa

import optparse
import re, os.path, sys
import GenomeAccess
from GeneModelFiles import load_gene_models
from variant_annotation.annotator import VariantAnnotator as VariantAnnotation
from utilities import *

def set_order(option, opt_str, value, parser):
    setattr(parser.values, option.dest, value)
    if not hasattr(parser.values, 'order'):
        parser.values.order = []
    parser.values.order.append(option.dest)

def get_argument_parser():
    desc = """Program to annotate variants (substitutions & indels & cnvs)"""
    parser = optparse.OptionParser(version='%prog version 2.2 10/October/2013', description=desc)
    parser.add_option('-c', help='chromosome column number/name', action='store')
    parser.add_option('-p', help='position column number/name', action='store')
    parser.add_option('-x', help='location (chr:pos) column number/name', action='store')
    parser.add_option('-v', help='variant column number/name', action='store')
    parser.add_option('-a', help='alternative allele (FOR SUBSTITUTIONS ONLY) column number/name', action='store')
    parser.add_option('-r', help='reference allele (FOR SUBSTITUTIONS ONLY) column number/name', action='store')
    parser.add_option('-t', help='type of mutation column number/name', action='store')
    parser.add_option('-q', help='seq column number/name', action='store')
    parser.add_option('-l', help ='length column number/name', action='store')

    parser.add_option('-P', help='promoter length', default=0, action='store', type='int', dest = "prom_len")
    parser.add_option('-H',help='no header in the input file', default=False,  action='store_true', dest='no_header')

    parser.add_option('-T', help='gene models ID <RefSeq, CCDS, knownGene>', type='string', action='store')
    parser.add_option('--Traw', help='outside gene models file path', type='string', action='store')
    parser.add_option('--TrawFormat', help='outside gene models format (refseq, ccds, knowngene)', type='string', action='store')

    parser.add_option('-G', help='genome ID <GATK_ResourceBundle_5777_b37_phiX174, hg19> ', type='string', action='store')
    parser.add_option('--Graw', help='outside genome file', type='string', action='store')

    parser.add_option('-I', help='geneIDs mapping file; use None for no gene name mapping', default="default", type='string', action='store')

    parser.add_option('--effect-type', help='name to use for effect type column', type='string', action='callback', callback=set_order)
    parser.add_option('--effect-gene', help='name to use for effect gene column', type='string', action='callback', callback=set_order)
    parser.add_option('--effect-details', help='name to use for effect details column', type='string', action='callback', callback=set_order)

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
