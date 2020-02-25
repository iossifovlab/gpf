#!/usr/bin/env python

import sys
import optparse
import os.path
import time
import datetime

from dae.gpf_instance.gpf_instance import GPFInstance

from dae import GenomeAccess
from dae.GeneModelFiles import load_gene_models
from dae.variant_annotation.annotator import (
    VariantAnnotator as VariantAnnotation,
)


start = time.time()

gpf_instance = GPFInstance()
genomes_db = gpf_instance.genomes_db


desc = """Program to annotate variants (substitutions & indels & cnvs)"""
parser = optparse.OptionParser(
    version="%prog version 2.2 10/October/2013",
    description=desc,
    add_help_option=False,
)
parser.add_option("-h", "--help", default=False, action="store_true")
parser.add_option("-c", help="chromosome column number/name", action="store")
parser.add_option("-p", help="position column number/name", action="store")
parser.add_option(
    "-x", help="location (chr:pos) column number/name", action="store"
)
parser.add_option("-v", help="variant column number/name", action="store")
parser.add_option(
    "-a",
    help="alternative allele (FOR SUBSTITUTIONS ONLY) column number/name",
    action="store",
)
parser.add_option(
    "-r",
    help="reference allele (FOR SUBSTITUTIONS ONLY) column number/name",
    action="store",
)
parser.add_option(
    "-t", help="type of mutation column number/name", action="store"
)
parser.add_option("-q", help="seq column number/name", action="store")
parser.add_option("-l", help="length column number/name", action="store")

parser.add_option(
    "-P",
    help="promoter length",
    default=0,
    action="store",
    type="int",
    dest="prom_len",
)
parser.add_option(
    "-H",
    help="no header in the input file",
    default=False,
    action="store_true",
    dest="no_header",
)

parser.add_option(
    "-T",
    help="gene models ID <RefSeq, CCDS, knownGene>",
    type="string",
    action="store",
)
parser.add_option(
    "--Traw",
    help="outside gene models file path",
    type="string",
    action="store",
)
parser.add_option(
    "--TrawFormat",
    help="outside gene models format (refseq, ccds, knowngene)",
    type="string",
    action="store",
)

parser.add_option(
    "-G",
    help="genome ID <GATK_ResourceBundle_5777_b37_phiX174, hg19> ",
    type="string",
    action="store",
)
parser.add_option(
    "--Graw", help="outside genome file", type="string", action="store"
)

(opts, args) = parser.parse_args()

if opts.help:
    print("\n------------------------------------------------------------\n")
    print("Program to annotate genomic variants - by Ewa, v2.2, 10/Oct/2013")
    print("BASIC USAGE: annotate_variant.py INFILE <OUTFILE> <options>\n")
    print(
        "-h, --help                       " "show this help message and exit"
    )
    print("-c CHROM                         " "chromosome column number/name ")
    print("-p POS                           " "position column number/name")
    print(
        "-x LOC                           "
        "location (chr:pos) column number/name "
    )
    print("-v VAR                           " "variant column number/name ")
    print(
        "-a ALT                           "
        "alternative allele (FOR SUBSTITUTIONS ONLY) column number/name"
    )
    print(
        "-r REF                           "
        "reference allele (FOR SUBSTITUTIONS ONLY) column number/name"
    )
    print(
        "-t TYPE                          "
        "type of mutation column number/name "
    )
    print("-q SEQ                           " "seq column number/name ")
    print("-l LEN                           " "length column number/name")
    print("-P PROM_LEN                      " "promoter length ")
    print("-H                               " "no header in the input file ")
    print(
        "-T T                             "
        "gene models ID <RefSeq, CCDS, knownGene> "
    )
    print("--Traw=TRAW                      " "outside gene models file path")
    print(
        "--TrawFormat=TRAWFORMAT          "
        "outside gene models format (refseq, ccds, knowngene)"
    )
    print(
        "-G G                             "
        "genome ID (GATK_ResourceBundle_5777_b37_phiX174, hg19)"
    )
    print("--Graw=GRAW                      " "outside genome file ")
    print(
        "-I I                             "
        "geneIDs mapping file; use None for no gene name mapping "
    )
    print("\n------------------------------------------------------------\n")
    sys.exit(0)


infile = "-"
outfile = None

if len(args) > 0:
    infile = args[0]

if infile != "-" and not os.path.exists(infile):
    sys.stderr.write("The given input file does not exist!\n")
    sys.exit(-78)

if len(args) > 1:
    outfile = args[1]
if outfile == "-":
    outfile = None

if infile == "-":
    variantFile = sys.stdin
else:
    variantFile = open(infile)

if not opts.no_header:
    first_line_str = variantFile.readline()
    first_line = first_line_str.split()
else:
    first_line = None


def give_column_number(s, header):
    try:
        c = header.index(s)
        return c + 1
    except Exception:
        sys.stderr.write(
            "Used parameter: " + s + " does NOT exist in the "
            "input file header\n"
        )
        sys.exit(-678)


def assign_values(param):
    if param is None:
        return param
    try:
        param = int(param)
    except Exception:
        if first_line is None:
            sys.stderr.write(
                "You cannot use column names when the file doesn't have a "
                "header (-H option set)!\n"
            )
            sys.exit(-49)
        param = give_column_number(param, first_line)
    return param


if opts.x is None and opts.c is None:
    opts.x = "location"
if (opts.v is None and opts.a is None) and (opts.v is None and opts.t is None):
    opts.v = "variant"


chrCol = assign_values(opts.c)
posCol = assign_values(opts.p)
locCol = assign_values(opts.x)
varCol = assign_values(opts.v)
altCol = assign_values(opts.a)
refCol = assign_values(opts.r)
typeCol = assign_values(opts.t)
seqCol = assign_values(opts.q)
lengthCol = assign_values(opts.l)

if opts.G is None and opts.Graw is None:
    GA = genomes_db.get_genome()
    if opts.T is None and opts.Traw is None:
        gmDB = genomes_db.get_gene_models()
    elif opts.Traw is None:
        gmDB = genomes_db.get_gene_models(opts.T)
    else:
        gmDB = load_gene_models(opts.Traw, None, opts.TrawFormat)


elif opts.Graw is None:
    GA = genomes_db.get_genome(opts.G)
    if opts.T is None and opts.Traw is None:
        gmDB = genomes_db.get_gene_models(genomeId=opts.G)
    elif opts.Traw is None:
        gmDB = genomes_db.get_gene_models(opts.T, genomeId=opts.G)
    else:
        gmDB = load_gene_models(opts.Traw, None, opts.TrawFormat)

else:
    GA = GenomeAccess.openRef(opts.Graw)
    if opts.Traw is None:
        print(
            "This genome requires gene models (--Traw option)", file=sys.stderr
        )
        sys.exit(-783)
    gmDB = load_gene_models(opts.Traw, None, opts.TrawFormat)


if "1" in GA.allChromosomes and "1" not in gmDB._utrModels.keys():
    gmDB.relabel_chromosomes()


sys.stderr.write("GENOME: " + GA.genomicFile + "\n")

sys.stderr.write("GENE MODEL FILES: " + gmDB.location + "\n")

if outfile is not None:
    out = open(outfile, "w")

if not opts.no_header:
    if outfile is None:
        print(first_line_str[:-1] + "\teffectType\teffectGene\teffectDetails")
    else:
        out.write(
            first_line_str[:-1] + "\teffectType\teffectGene\teffectDetails\n"
        )

argColumnNs = [
    chrCol,
    posCol,
    locCol,
    varCol,
    refCol,
    altCol,
    lengthCol,
    seqCol,
    typeCol,
]

sys.stderr.write("...processing....................\n")
k = 0

annotator = VariantAnnotation(GA, gmDB, promoter_len=opts.prom_len)

for l in variantFile:
    if l[0] == "#":
        if outfile is None:
            print(l, end="")
        else:
            out.write(l)
        continue
    k += 1
    if k % 1000 == 0:
        sys.stderr.write(str(k) + " lines processed\n")

    line = l[:-1].split("\t")
    params = [line[i - 1] if i is not None else None for i in argColumnNs]

    effects = annotator.do_annotate_variant(*params)
    desc = annotator.effect_description(effects)

    if outfile is None:
        print(l[:-1] + "\t" + "\t".join(desc))
    else:
        out.write(l[:-1] + "\t" + "\t".join(desc) + "\n")

if infile != "-":
    variantFile.close()

if outfile is not None:
    out.write("# PROCESSING DETAILS:\n")
    out.write("# " + time.asctime() + "\n")
    out.write("# " + " ".join(sys.argv) + "\n")
    sys.stderr.write("Output file saved as: " + outfile + "\n")
else:
    print(
        "# PROCESSING DETAILS:\n# "
        + time.asctime()
        + "\n# "
        + " ".join(sys.argv)
    )


if outfile is not None:
    out.close()


sys.stderr.write(
    "The program was running for [h:m:s]: "
    + str(datetime.timedelta(seconds=round(time.time() - start, 0)))
    + "\n"
)
