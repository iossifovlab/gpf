#!/usr/bin/env python

# Oct 9th 2013
# written by Ewa

import optparse
import re, os.path
import GenomeAccess
from GeneModelFiles import *
from variant_annotation.annotator import VariantAnnotator as VariantAnnotation
import time
import datetime
from DAE import *

def set_order(option, opt_str, value, parser):
    setattr(parser.values, option.dest, value)
    if not hasattr(parser.values, 'order'):
        parser.values.order = []
    parser.values.order.append(option.dest)

def get_argument_parser():
    desc = """Program to annotate variants (substitutions & indels & cnvs)"""
    parser = optparse.OptionParser(version='%prog version 2.2 10/October/2013', description=desc, add_help_option=False)
    parser.add_option('-h', '--help', default=False, action='store_true')
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

    parser.add_option('--effect-type', type='string', action='callback', callback=set_order)
    parser.add_option('--effect-gene', type='string', action='callback', callback=set_order)
    parser.add_option('--effect-details', type='string', action='callback', callback=set_order)

    return parser

def print_help():
    print("\n\n----------------------------------------------------------------\n\nProgram to annotate genomic variants - by Ewa, v2.2, 10/Oct/2013" )
    print("BASIC USAGE: annotate_variant.py INFILE <OUTFILE> <options>\n")
    print("-h, --help                       show this help message and exit")
    print("-c CHROM                         chromosome column number/name ")
    print("-p POS                           position column number/name")
    print("-x LOC                           location (chr:pos) column number/name ")
    print("-v VAR                           variant column number/name ")
    print("-a ALT                           alternative allele (FOR SUBSTITUTIONS ONLY) column number/name")
    print("-r REF                           reference allele (FOR SUBSTITUTIONS ONLY) column number/name")
    print("-t TYPE                          type of mutation column number/name ")
    print("-q SEQ                           seq column number/name ")
    print("-l LEN                           length column number/name")
    print("-P PROM_LEN                      promoter length ")
    print("-H                               no header in the input file ")
    print("-T T                             gene models ID <RefSeq, CCDS, knownGene> ")
    print("--Traw=TRAW                      outside gene models file path")
    print("--TrawFormat=TRAWFORMAT          outside gene models format (refseq, ccds, knowngene)")
    print("-G G                             genome ID (GATK_ResourceBundle_5777_b37_phiX174, hg19)")
    print("--Graw=GRAW                      outside genome file ")
    print("-I I                             geneIDs mapping file; use None for no gene name mapping ")

    print("\n----------------------------------------------------------------\n\n")

def give_column_number(s, header):
    try:
        c = header.index(s)
        return(c+1)
    except:
        sys.stderr.write("Used parameter: " + s + " does NOT exist in the input file header\n")
        sys.exit(-678)


def assign_values(param, header=None):
    if param == None:
        return(param)
    try:
        param = int(param)
    except:
        if header == None:
            sys.stderr.write("You cannot use column names when the file doesn't have a header (-H option set)!\n")
            sys.exit(-49)
        param = give_column_number(param, header)
    return(param)

class EffectAnnotator(object):

    def __init__(self, opts, header=None):
        self.opts = opts
        self.header = header
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

    def annotate_file(self, input, output):
        if self.opts.no_header == False:
            output.write("\t".join(self.header) + "\n")

        sys.stderr.write("...processing....................\n")
        k = 0

        for l in input:
            if l[0] == "#":
                output.write(l)
                continue
            k += 1
            if k%1000 == 0:
                sys.stderr.write(str(k) + " lines processed\n")

            line = l[:-1].split("\t")
            line_annotations = self.line_annotations(line, self.opts.order)
            line.extend(line_annotations)

            output.write("\t".join(line) + "\n")

    def line_annotations(self, line, new_cols_order):
        params = [line[i-1] if i!=None else None for i in self.argColumnNs]

        effects = self.annotation_helper.do_annotate_variant(*params)
        effect_type, effect_gene, effect_details = self.annotation_helper.effect_description(effects)

        return [locals()[col] for col in new_cols_order]


def main():
    start=time.time()

    (opts, args) = get_argument_parser().parse_args()

    if opts.help:
        print_help()
        sys.exit(0)


    infile = '-'
    outfile = None

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
        first_line_str = variantFile.readline()
        first_line = first_line_str.split()
    else:
        first_line = None

    if outfile != None:
        out = open(outfile, 'w')
    else:
        out = sys.stdout


    annotator = EffectAnnotator(opts=opts, header=first_line)
    annotator.annotate_file(variantFile, out)

    out.write("# PROCESSING DETAILS:\n")
    out.write("# " + time.asctime() + "\n")
    out.write("# " + " ".join(sys.argv[1:]) + "\n")


    if infile != '-':
        variantFile.close()

    if outfile != None:
        out.close()
        sys.stderr.write("Output file saved as: " + outfile + "\n")


    sys.stderr.write("The program was running for [h:m:s]: " + str(datetime.timedelta(seconds=round(time.time()-start,0))) + "\n")


if __name__ == "__main__":
    main()
