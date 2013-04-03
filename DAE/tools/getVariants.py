#!/bin/env python

import argparse
import itertools 

from DAE import *
print "hi"

parser = argparse.ArgumentParser(description="Query denovo and inheritted variants.")
parser.add_argument('--denovoStudies', type=str, 
        default="allPublishedPlusOurRecent",
        help='the sutdies to query for denovo variants')
parser.add_argument('--transmittedStudy', type=str, default="wig683",
        help='the sutdy to query the transmitted variants')
parser.add_argument('--effectTypes', type=str, default="LGDs", 
        help='effect types (i.e. LGDs,missense,synonymous,frame-shift). LGDs by default. none for all variants')
parser.add_argument('--variantTypes', type=str, 
        help='variant types (i.e. sub or ins,del)')
parser.add_argument('--popFrequencyMax', type=str, default="1.0",
        help='maximum population frequency in percents. Can be 100 or -1 for no limit; ultraRare. 1.0 by default.')
parser.add_argument('--popFrequencyMin', type=str, default="-1",
        help='minimum population frequency in percents. Can be -1 for no limit. -1 by default.')
parser.add_argument('--inChild', type=str, 
        help='i.e. prb, sib, prbM, sibF')
parser.add_argument('--familiesFile', type=str, 
        help='list of the families to report')
parser.add_argument('--geneSym', type=str, help='list of gene syms')
parser.add_argument('--geneSymFile', type=str, help='the first column should cotain gene symbols')
parser.add_argument('--geneId', type=str, help='list of gene ids')
parser.add_argument('--geneIdFile', type=str, help='the first column should cotain gene ids')
parser.add_argument('--regionS', type=str, help='region')
args = parser.parse_args()

print args

def loadTextColumn(colSpec):
    cn = 0
    sepC = "\t"
    header = 1
    cs = colSpec.split(',')
    fn = cs[0]
    if len(cs)>1:
        cn = int(cs[1])
    if len(cs)>2:
        sepC = cs[2]
    if len(cs)>3:
        header = int(cs[3])
    f = open(fn)
    if header == 1:
        f.readline()

    r = []
    for l in f:
        cs = l.strip().split(sepC)
        r.append(cs[cn])        
    return r

families = None
if args.familiesFile:
    families = loadTextColumn(args.familiesFile)

geneSyms = None

if args.geneSym:
    geneSyms = set(args.geneSym.split(","))

if args.geneSymFile:
    geneSyms = set(loadTextColumn(args.geneSymFile))

geneIds = None
if args.geneId:
    geneIds = set(args.geneId.split(","))

if args.geneId:
    geneIds = set(loadTextColumn(args.geneIdFile))

if geneIds:
    geneSyms = { giDB.genes[x].sym for x in geneIds if x in giDB.genes }

# regionS
# regionSFile

effectTypes = None
if args.effectTypes != "none":
    effectTypes = args.effectTypes
    
dvs = []
if args.denovoStudies:
    dvs = vDB.get_denovo_variants(vDB.get_studies(args.denovoStudies),
                    inChild=args.inChild, variantTypes=args.variantTypes, effectTypes=effectTypes,
                    familyIds=families,geneSyms=geneSyms,regionS=args.regionS)

ivs = []
if args.transmittedStudy:
    popFreqMax = -1
    ultraRare = False 
    if args.popFrequencyMax=="ultraRare":
        ultraRare = True
    else:
        popFreqMax = float(args.popFrequencyMax)
    ist = vDB.get_study(args.transmittedStudy)
    ivs = ist.get_transmitted_variants(variantTypes=args.variantTypes, effectTypes=effectTypes,
                        inChild=args.inChild,
                        minParentsCalled=float(args.popFrequencyMin),
                        maxAltFreqPrcnt=popFreqMax,
                        ultraRareOnly=ultraRare,
                        familyIds=families,geneSyms=geneSyms,regionS=args.regionS)

safeVs(itertools.chain(dvs,ivs),'aaaaa.txt',['all.altFreq','all.nAltAlls'])
