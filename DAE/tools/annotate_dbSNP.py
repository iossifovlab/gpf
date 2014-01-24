#!/bin/env python

# Jan 21th 2014
# by Ewa

from dbSNP import *
from VariantAnnotation import load_variant
import sys
import time
import optparse
import os

start=time.time()

desc = """Program to annotate genetic variants with dbSNP"""
parser = optparse.OptionParser(version='%prog version 1.0 21/January/2014', description=desc, add_help_option=False)
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

parser.add_option('-F', help='dbSNP file', default="/data/unsafe/autism/genomes/hg19/dbSNP/dbSNP_138.hdf5", action='store') #
parser.add_option('-C', help='dbSNP column numbers to annotate with', default="5", action='store')
parser.add_option('-H',help='no header in the input file', default=False,  action='store_true', dest='no_header')



(opts, args) = parser.parse_args()

if opts.help:
    print("\n\n----------------------------------------------------------------\n\n" + desc )
    print("BASIC USAGE: " + sys.argv[0] + " INFILE <OUTFILE> <options>\n")
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

    print("-F FILE                          dbSNP file (/data/unsafe/autism/genomes/hg19/dbSNP/snp138.txt.gz by default)")
    print("-C,                              dbSNP column numbers to annotate with: a string separated by colons ('5' by default)")
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
        param = int(param)
    except:
        if first_line == None:
            sys.stderr.write("You cannot use column names when the file doesn't have a header (-H option set)!\n")
            sys.exit(-49)
        param = give_column_number(param, first_line)
    return(param)



if opts.x == None and opts.c == None:
    opts.x = "location"
if (opts.v == None and opts.a == None) and (opts.v == None and opts.t == None):
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



opts.C = opts.C.replace(" ", "")
db_columns = map(int, opts.C.split(":"))


db_snp = load_dbSNP(file=opts.F)


if outfile != None:
    out = open(outfile, 'w')

if opts.no_header == False:
    score_names = db_snp.Scores[db_snp.Scores.keys()[0]].dtype.names
    cols_header = "\t".join([score_names[i-1] for i in db_columns])
    if outfile == None:
        print(first_line_str[:-1] + "\t" + cols_header) #
    else:
        out.write(first_line_str[:-1] + "\t" + cols_header + "\n") 

argColumnNs = [chrCol, posCol, locCol, varCol, refCol, altCol]

sys.stderr.write("...processing....................\n")
chr_format = None
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
    params = [line[i-1] if i != None else None for i in argColumnNs]

    if chr_format == None:
        if params[0] == None:
            chr = params[3].split(":")[0]
        else:
            chr = params[0]
        if chr.startswith("chr"):
            chr_format = "hg19"
        else:
            chr_format = "GATK"
            db_snp.relabel_chromosomes()

    res_vars = db_snp.find_variant(*params)

    if res_vars == []:
            des ="\t" * len(db_columns)
    else:
        des = ""
        for c in db_columns:
            for i in res_vars:
                des += str(i[c-1]) + "|"
            des = des[:-1] + "\t"
        des = des[:-1]
        
            

    if outfile == None:
        print(l[:-1] + "\t" + des)
    else:
        out.write(l[:-1] + "\t" + des + "\n")

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





    
