#!/bin/env python

# Dec 12th 2013
# by Ewa

from DAE import *
from GenomicScores import *
import optparse
import time

start=time.time()

desc = """Program to annotate genomic positions with genomic scores (GERP, PhyloP, phastCons, nt, GC, cov)"""
parser = optparse.OptionParser(version='%prog version 1.0 12/December/2013', description=desc, add_help_option=False)
parser.add_option('-h', '--help', default=False, action='store_true')
parser.add_option('-c', help='chromosome column number/name', action='store')
parser.add_option('-p', help='position column number/name', action='store')
parser.add_option('-x', help='location (chr:pos) column number/name', action='store')
parser.add_option('-F', help='genomic score file', action='store')
parser.add_option('-S', help='scores subset [string - colon separated]', action='store')
parser.add_option('-H',help='no header in the input file', default=False,  action='store_true', dest='no_header')



(opts, args) = parser.parse_args()

if opts.help:
    print("\n\n----------------------------------------------------------------\n\n" + desc )
    print("BASIC USAGE: annotate_with_genomic_scores.py INFILE <OUTFILE> <options>\n")
    print("-h, --help                       show this help message and exit")
    print("-c CHROM                         chromosome column number/name ")
    print("-p POS                           position column number/name")
    print("-x LOC                           location (chr:pos) column number/name ")
    print("-F FILE                          genomic score file path")
    print("-S FILE                          scores subset: string colon separated")
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


chrCol = assign_values(opts.c)
posCol = assign_values(opts.p)
locCol = assign_values(opts.x)


All_lines = []
All_locs = []
for l in variantFile:
    All_lines.append(l)
    if l[0] == "#":
       #All_locs.append(None)
       continue
    line = l[:-1].split("\t")
    if locCol:
        All_locs.append(line[locCol])
    else:
        All_locs.append(line[chrCol] + ":" + line[posCol])




gs = load_genomic_scores(opts.F)
if opts.S != None:
    scores = opts.S.split(";")
else:
    scores = gs._score_names
res = gs.get_multi_score(All_locs, scores=scores)



if outfile != None:
    out = open(outfile, 'w')



if opts.no_header == False:
    header_line = "\t".join([gs.name + ":" + s for s in scores])
    if outfile == None:
        print(first_line_str[:-1] + "\t" + header_line)
    else:
        out.write(first_line_str[:-1] + "\t" + header_line + "\n")
sys.stderr.write("...processing....................\n")

   
    
    
k = 0
for l in All_lines:
    if l[0] == "#":
        if outfile == None:
            print l,
        else:
            out.write(l)
        k+=1
        continue
    s = map(str,[a for a in res[k]])
    if s == []:
        s = ['NA']*len(scores)
    if outfile == None:
        print(l[:-1] + "\t" + "\t".join(s))
    else:
        out.write(l[:-1] + "\t" + "\t".join(s) + "\n")
    k += 1


if infile != '-':
    variantFile.close()

if outfile != None:
    out.write("# PROCESSING DETAILS:\n")
    out.write("# " + time.asctime() + "\n")
    out.write("# " + " ".join(sys.argv) + "\n")
    sys.stderr.write("Output file saved as: " + outfile + "\n")
else:
    sys.stderr.write("# PROCESSING DETAILS:\n# " + time.asctime() + "\n# " + " ".join(sys.argv) + "\n")
    

if outfile != None:
    out.close()
