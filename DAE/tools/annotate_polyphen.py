#!/bin/env python

# Jan 8th 2014
# by Ewa

import optparse
from Polyphen import *
import os
import time
import datetime

start=time.time()

desc = """Program to annotate SNPs with polyphen scores """
parser = optparse.OptionParser(version='%prog version 2.0 7/January/2014', description=desc, add_help_option=False)
parser.add_option('-h', '--help', default=False, action='store_true')
parser.add_option('-c', help='chromosome column number/name', action='store')
parser.add_option('-p', help='position column number/name', action='store')
parser.add_option('-x', help='location (chr:pos) column number/name', action='store')
parser.add_option('-v', help='variant column number/name', action='store')
parser.add_option('-a', help='alternative allele (FOR SUBSTITUTIONS ONLY) column number/name', action='store')
parser.add_option('-r', help='reference allele (FOR SUBSTITUTIONS ONLY) column number/name', action='store')

parser.add_option('-H',help='no header in the input file', default=False,  action='store_true', dest='no_header')

(opts, args) = parser.parse_args()

if opts.help:
    print("\n\n----------------------------------------------------------------\n\nProgram to annotate SNPs with polyphen scores - by Ewa, v2.0, 7/January/2014" )
    print("BASIC USAGE: annotate_polyphen.py INFILE <OUTFILE> <options>\n")
    print("-h, --help                       show this help message and exit")
    print("-c CHROM                         chromosome column number/name ")
    print("-p POS                           position column number/name")
    print("-x LOC                           location (chr:pos) column number/name ")
    print("-v VAR                           variant column number/name ")
    print("-a ALT                           alternative allele (FOR SUBSTITUTIONS ONLY) column number/name")
    print("-r REF                           reference allele (FOR SUBSTITUTIONS ONLY) column number/name")
    print("-H                               no header in the input file ")
    print("\n----------------------------------------------------------------\n\n")
    sys.exit(0)

infile = '-'
outfile = None

if len(args) > 0:
    infile = args[0]

if infile != '-' and os.path.exists(infile) == False:
    raise Exception("The given input file does not exist!")

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

    
def give_column_number(s, header):
    try:
        c = header.index(s)
        return(c+1)
    except:
        sys.stderr.write("Used parameter: " + s + " does NOT exist in the input file header\n")
        sys.exit(-678)


def assign_values(param):
    if param == None:
        return(param)
    try:
        param = int(param) - 1
    except:
        if first_line == None:
            sys.stderr.write("You cannot use column names when the file doesn't have a header (-H option set)!\n")
            sys.exit(-49)
        param = give_column_number(param, first_line) - 1
    return(param)


if opts.x == None and opts.c == None:
    opts.x = "location"
if (opts.v == None and opts.a == None):
    opts.v = "variant"

chrCol = assign_values(opts.c)
posCol = assign_values(opts.p)
locCol = assign_values(opts.x)
varCol = assign_values(opts.v)
altCol = assign_values(opts.a)
refCol = assign_values(opts.r)

if outfile != None:
    out = open(outfile, 'w')

sys.stderr.write("...processing polyphen...............\n")

PP = load_polyphen()

file_header = "hdiv_pred\thdiv_prob_hvar_pred\thvar_prob"

if opts.no_header == False:
    if outfile == None:
        print(first_line_str[:-1] + "\t" + file_header)
    else:
        out.write(first_line_str[:-1] + "\t" + file_header + "\n")

k = 0
for l in variantFile:
    if l[0] == "#":
        if outfile == None:
            print l,
        else:
            out.write(l)
        continue
    k += 1
    if k%1000 == 0:
        sys.stderr.write(str(k) + " lines processed\n")

    line = l[:-1].split("\t")

    if locCol != None:
        loc = line[locCol]
    else:
        chrom = line[chrCol]
        position = line[posCol]
        loc = chrom + ":" + position
    if loc.startswith("chr") == False:
        chrom = "chr" + chrom

    if varCol != None:
        variant = line[varCol]
    else:
        ref_allele = line[refCol]
        alt_allele = line[altCol]
        variant = "sub(" + ref_allele + "->" + alt_allele + ")"

    pp_res = PP.get_variant(loc, variant)
    if pp_res == None:
        desc = "\t\t\t"
    else:
        desc = pp_res.hdiv_pred + "\t" + str(pp_res.hdiv_prob) + "\t" + pp_res.hvar_pred+ "\t" + str(pp_res.hvar_prob)

    if outfile == None:
        print(l[:-1] + "\t" + desc)
    else:
        out.write(l[:-1] + "\t" + desc + "\n")

if infile != '-':
    variantFile.close()

if outfile != None:
    out.write("# PROCESSING DETAILS:\n")
    out.write("# " + time.asctime() + "\n")
    out.write("# " + " ".join(sys.argv) + "\n")
    sys.stderr.write("Output file saved as: " + outfile + "\n")
else:
    print("# PROCESSING DETAILS:\n# " + time.asctime() + "\n# " + " ".join(sys.argv))
    

if outfile != None:
    out.close()


sys.stderr.write("The program was running for [h:m:s]: " + str(datetime.timedelta(seconds=round(time.time()-start,0))) + "\n")

    



        
