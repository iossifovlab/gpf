#!/bin/env python

from subprocess import Popen
from subprocess import PIPE 
import sys

# inFile = sys.argv[1]
# outFile = sys.argv[2]


# print "inFile:", inFile
# f = Popen(["annotate_variants.py", inFile], stdout=PIPE).stdout
f = sys.stdin

hdrCs = f.readline().strip().split("\t")
# print "\n".join(hdrCs)

map = {}
for c in [-1, -2, -3]:
    map[c] = hdrCs.index(hdrCs[c])
del hdrCs[-3:]

print "\t".join(hdrCs)

for l in f:
    if l[0]=='#':
        print l,
        break
    cs = l.strip().split("\t")
    for fc,tc in map.items():
        cs[tc] = cs[fc]
    del cs[-3:]
    print "\t".join(cs)

# print map
