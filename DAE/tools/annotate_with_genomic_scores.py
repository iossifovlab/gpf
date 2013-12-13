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
parser.add_option('-p', help='position column number/name', action='store')
parser.add_option('-x', help='location (chr:pos) column number/name', action='store')
parser.add_option('-H',help='no header in the input file', default=False,  action='store_true', dest='no_header')
parser.add_option('-A',help='annotate with all scores', default=False,  action='store_true')
parser.add_option('-C',help='annotate with conservation scores only (GERP, phyloP, phastCons) - SET BY DEFAULT', default=False,  action='store_true')
parser.add_option('-L',help='all scores listed as a string separated by ";"', type='string')


(opts, args) = parser.parse_args()

if opts.help:
    print("\n\n----------------------------------------------------------------\n\n" + desc )
    print("BASIC USAGE: annotate_with_genomic_scores.py INFILE <OUTFILE> <options>\n")
    print("-h, --help                       show this help message and exit")
    print("-c CHROM                         chromosome column number/name ")
    print("-p POS                           position column number/name")
    print("-x LOC                           location (chr:pos) column number/name ")
    print("-H                               no header in the input file ")
    print("-A                               annotate with all scores")
    print("-C                               annotate with conservation scores only - DEFAULT OPTION")
    print("-L                               annotate with all scores listed as a string separated by ';'")
    print("\n----------------------------------------------------------------\n\n")
    sys.exit(0)



infile = '-'
outfile = None

if len(args) > 0:
    infile = args[0]

if infile != '-' and os.path.exists(infile) == False:
    raise Exception("The given input file does not exist!")

if opts.A == None and opts.L == None:
    opts.C = True

if (opts.A != None and opts.C != None) or (opts.A != None and opts.L != None) or (opts.C != None and opts.L != None):
    raise Exception("You can only choose one parameter from -A, -C and -L!")




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


chrCol = assign_values(opts.c)
posCol = assign_values(opts.p)
locCol = assign_values(opts.x)

if outfile != None:
    out = open(outfile, 'w')

if opts.no_header == False:
    if outfile == None:
        print(first_line_str[:-1] + "\teffectType\teffectGene\teffectDetails") ###? [NAME OF THE SCORES]
    else:
        out.write(first_line_str[:-1] + "\teffectType\teffectGene\teffectDetails\n") ###? [NAME OF THE SCORES]

sys.stderr.write("...processing....................\n")


# general function: load_gerp............

All_locs = []
for l in variantFile:
    if l[0] == "#":
       All_locs.append(None) 
    line = l[:-1].split("\t")
    if locCol:
        All_locs.append(line[locCol])
    else:
        All_locs.append(line[chrCol] + ":" + line[posCol])


    

    #??
    # LIST OF LINES=POSITIONS? parallel?
Res = []
if opts.C:
    # load_gerp
    gs = load_genomic_scores("/mnt/wigclust5/data/safe/egrabows/2013/Modules/gerp.npz")
    res = gs.get_multi_score(all_locs)
    Res.append(res)
    # load_pp
    gs = load_genomic_scores("/mnt/wigclust5/data/safe/egrabows/2013/Modules/phyloP.npz")
    res = gs.get_multi_score(all_locs)
    Res.append(res)
    # load_phastcons
    gs = load_genomic_scores("/mnt/wigclust5/data/safe/egrabows/2013/Modules/phastCons.npz")
    res = gs.get_multi_score(all_locs)
    Res.append(res)
    
    
k = 0
for l in variantFile:
    if l[0] == "#":
        if outfile == None:
            print l,
        else:
            out.write(l)
        k+=1
        continue
    s = [a for b in [x[k] for x in Res] for a in b]
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
    print("# PROCESSING DETAILS:\n# " + time.asctime() + "\n# " + " ".join(sys.argv))
    

if outfile != None:
    out.close()
