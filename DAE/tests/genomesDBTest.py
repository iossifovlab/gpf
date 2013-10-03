#!/bin/env python

from DAE import *

print genomesDB

GA = genomesDB.get_genome()
GA2 = genomesDB.get_genome('hg19')

print GA.getSequence("1", 1000000,1000010)
print GA2.getSequence("chr1", 1000000,1000010)


gm = genomesDB.get_gene_models()

print "hurrey"
