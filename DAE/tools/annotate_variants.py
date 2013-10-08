#!/bin/env python

# Oct 7th 2013
# written by Ewa

import optparse
from subprocess import call
import re, os.path
import GenomeAccess
from GeneModelFiles import *
import VariantAnnotation
import VariantAnnotation_mito
import time
import datetime

start=time.time()

desc = """Program to annotate variants (substitutions & indels & cnvs)"""
parser = optparse.OptionParser(version='%prog version 2.1 07/October/2013', description=desc)
parser.add_option('-f', help='input file path [MANDATORY FIELD!]', action='store', type='string', dest='inputFile')
parser.add_option('-o', help='output file path [MANDATORY FIELD!]', action='store', type='string', dest='outputFile')
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
parser.add_option('-H', help='no header in the input file', default=False,  action='store_true', dest='no_header')
parser.add_option('-T', help='gene model file path [refseq by default]', default="/data/unsafe/autism/genomes/hg19/geneModels/refGene.txt.gz"  , type='string', action='store')
parser.add_option('-C', help='mitochondrial gene model file path [mitomap by default]', default="/data/unsafe/autism/genomes/hg19/geneModels/mitomap.txt"  , type='string', action='store') 

parser.add_option('-G', help='genome seq fasta file [GATK-hg19 by default]', default="/data/unsafe/autism/genomes/GATK_ResourceBundle_5777_b37_phiX174/chrAll.fa"  , type='string', action='store')
parser.add_option('-M', help='mitochondrial genome seq fasta file [GATK-hg19 by default]', default="/data/unsafe/autism/genomes/GATK_ResourceBundle_5777_b37_phiX174/chrAll.fa"  , type='string', action='store')
parser.add_option('-I', help='geneIDs mapping file [by default geneId files from /data/unsafe/autism/genomes/hg19/geneModels/]; use None for no gene name mapping', default="default"  , type='string', action='store')

(opts, args) = parser.parse_args()

if opts.inputFile == None:
    parser.error('Input filename not given')
if opts.outputFile == None:
    parser.error('Output filename not given')
if os.path.exists(opts.inputFile) == False:
    print("The given input file does not exist!")
    sys.exit(-78)

if opts.no_header == False:
    f = open(opts.inputFile)
    first_line = f.readline()
    f.close()
    first_line = first_line.split()
else:
    first_line = None
    

def give_column_number(s, header):
    try:
        c = header.index(s)
        return(c+1)
    except:
        print ("Used parameter: " + s + " does NOT exist in the input file header")
        sys.exit(-678)

def assign_values(param):
    if param == None:
        return(param)
    try:
        param = int(param)
    except:
        if first_line == None:
            print("You cannot use column names when the file doesn't have a header (-H option set)!")
            sys.exit(-49)
        param = give_column_number(param, first_line)
    return(param)

def deal_with_old_format(s):
    
    if "^" in s[1:-1] or "$" in s[1:-1]:
        if "$" in  s[1:-1]:
            r = re.match('(.*)\$[0-9]+', s)
            if r != None:
                s = r.group(1)
        if "^" in s[1:-1]:
            r = re.match('[0-9]+\^(.*)', s)
            if r != None:
                s = r.group(1)

    return(s)

        
chrCol = assign_values(opts.c)
posCol = assign_values(opts.p)
locCol = assign_values(opts.x)
varCol = assign_values(opts.v)
altCol = assign_values(opts.a)
refCol = assign_values(opts.r)
typeCol = assign_values(opts.t)
seqCol = assign_values(opts.q)
lengthCol = assign_values(opts.l)



def parseInputFileRow(line):


    global chrCol, posCol, locCol
    global varCol, altCol, refCol
    global typeCol, seqCol, lengthCol

    line = line[:-1].split("\t")
    try:
        loc = line[locCol-1].split(":")
        chr = loc[0]
        pos = loc[1]
    except:
        chr = line[chrCol-1]
        pos = line[posCol-1]

    try:
        seq = line[altCol-1]
        type = "S"
        length = 1
        try:
            ref = line[refCol-1]
        except:
            ref = None
            
    except:
        try:
            var = line[varCol-1]
            type = var[0].upper()
            x1 = var.index("(")
            x2 = var.index(")")
            var = var[x1+1:x2]
            if "^" in var or "$" in var:
                var = deal_with_old_format(var)
            
                if "^" == var[0] or "$" == var[-1]:
                    ref = seq  = None
                    length = 1
                    return(chr, int(pos), type, seq, length, ref)
            if type == "I":
                ref = None
                seq = re.sub('[0-9]+', '', var)
                
                length = len(seq)
            elif type == "D":
                ref = None
                seq = ""
                length = int(var)
            elif type == "S":
                ref = var[0]
                seq = var[-1]
                length = 1
            elif type == "C":
                type = var.upper()
                ref = None
                seq = var[-1]
                pos_start = pos.split("-")[0]                
                length = int(pos.split("-")[1])-int(pos_start) +1
                pos = pos_start
                
            else:
                print("Incorrect mutation variant: " + line[varCol-1])
                sys.exit(-32)

        except:
            type = line[typeCol-1][0].upper()
            if type == "D":
                seq = ""
                length = int(line[lengthCol-1])
                ref = None
            elif type == "S":
                seq = line[seqCol-1]
                length = 1
                ref = None
            elif type == "I":
                seq = re.sub('[0-9]+', '', line[seqCol-1])
                ref = None
                length = int(line[lengthCol-1])
                if "^" in seq or "$" in seq:
                    seq = deal_with_old_format(seq)
                    if "^" == seq[0] or "$" == seq[-1]: 
                        seq = None
            else:
                print("Incorrect mutation type: " + line[typeCol-1])
                sys.exit(-34)
             
    return(chr, int(pos), type, seq, length, ref)
        
        


if opts.x == None and opts.c == None:
    parser.error('Chromosome / location column number (-c/-x option) not given!')    
if opts.x == None and opts.p == None:
    parser.error('Position column number (-c option) not given!')
if opts.x and (opts.c or opts.p):
    parser.error('Redundant information. Please specify either -x option or both -c and -p options')
if (opts.v == None and opts.a == None) and (opts.v == None and (opts.t == None or opts.q == None or opts.l == None)):
    parser.error("""You must specify how variants are described in the input file! choose parameters from:
    \t1) -v (column format examples: sub(A->C), ins(AA), del(3), cnv+)
    \tor
    \t2) -a (for substitutions only)
    \tor
    \t3) -t -q -l (for indels)""")


gm = load_gene_models(opts.T, opts.I)

if opts.T == opts.C:
    gm_mit = gm
else:
    gm_mit = load_gene_models(opts.C, opts.I) 

    
ref_hg = GenomeAccess.openRef(opts.G)
if opts.G == opts.M:
    ref_mt = ref_hg
else:
    ref_mt = GenomeAccess.openRef(opts.M)


if "1" in ref_hg.allChromosomes:
    gm.relabel_chromosomes()

if "1" in ref_mt.allChromosomes:
    gm_mit.relabel_chromosomes()

variantFile = open(opts.inputFile)



resFile = open("tempRes.txt", 'w')

if opts.no_header == False:
    resFile.write("effectType\teffectGene\teffectDetails\n")
    line = variantFile.readline()


while True:
    line = variantFile.readline()
    if not line:
        break
    if line[0] == "#":
        resFile.write("\n")        
    


        continue
    
    chrom, pos, type, sequence, l, refNt = parseInputFileRow(line)
    
    if chrom in ["chrM", "M", "MT"]:
        v = VariantAnnotation_mito.load_variant(chr=chrom, position=pos, ref=refNt, length=l, seq=sequence, typ=type)
        effects = v.annotate(gm_mit, ref_mt, display=False)
        desc = VariantAnnotation_mito.effect_description(effects)
        resFile.write("\t".join(desc) + "\n")
    else:
        v = VariantAnnotation.load_variant(chr=chrom, position=pos, ref=refNt, length=l, seq=sequence, typ=type)
        effects = v.annotate(gm, ref_hg, display=False, promoter_len = opts.prom_len)
        desc = VariantAnnotation.effect_description(effects)
        resFile.write("\t".join(desc) + "\n")

variantFile.close()
resFile.close()
call("paste " + opts.inputFile + " tempRes.txt > " + opts.outputFile, shell=True)

os.remove("tempRes.txt")

file = open(opts.outputFile, 'a')
file.write("# PROCESSING DETAILS:\n")
file.write("# " + time.asctime() + "\n")
file.write("# " + " ".join(sys.argv) + "\n")

print("Output file saved as: " + opts.outputFile)
print("The program was running for [h:m:s]: " + str(datetime.timedelta(seconds=round(time.time()-start,0))))



