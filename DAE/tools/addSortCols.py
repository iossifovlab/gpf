#!/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
import sys

fmt = "dnv"
if len(sys.argv) > 1:
    fmt = sys.argv[1]

faiFN = "/data/unsafe/autism/genomes/GATK_ResourceBundle_5777_b37_phiX174/chrAll.fa.fai"
if len(sys.argv) > 2:
    faiFN = sys.argv[2]


chrInd = {}

FAIF = open(faiFN)
chrInd = { ln.split("\t")[0]:li  for li,ln in enumerate(FAIF) }
FAIF.close()


hdL = sys.stdin.readline()
print("-1\t", hdL, end=' ') 
hdCs = hdL.split("\t")

if fmt=="dnv":
    locCI = hdCs.index("location")
    varCI = hdCs.index("variant")
   
    for l in sys.stdin: 
        if l[0] == "#":
            continue
        cs = l.strip().split('\t')
        ch,pos = cs[locCI].split(":")
        if ch not in chrInd:
            continue
        chI = str(chrInd[ch])
        vr = cs[varCI]
        print("\t".join([chI,pos,vr,l]), end=' ')

elif fmt=="trm":
    chrCI = hdCs.index("chr")
    posCI = hdCs.index("position")
    varCI = hdCs.index("variant")
   
    for l in sys.stdin: 
        if l[0] == "#":
            continue
        cs = l.strip().split('\t')
        ch = cs[chrCI]
        if ch not in chrInd:
            continue
        pos = cs[posCI]
        chI = str(chrInd[ch])
        vr = cs[varCI]
        print("\t".join([chI,pos,vr,l]), end=' ')

else:
    print("Unknown format", fmt, file=sys.stderr)
