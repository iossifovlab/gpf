#!/bin/env python

from GeneModelFiles import *
import sys

fromGMFile = sys.argv[1]
toGMFile = sys.argv[2]
# chrMapFile = sys.argv[2]

gmDB = load_gene_models(fromGMFile)
gmDB.relabel_chromosomes()
save_dicts(gmDB, outputFile = toGMFile)
