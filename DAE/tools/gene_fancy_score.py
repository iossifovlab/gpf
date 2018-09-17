#!/bin/env python

# Jan 17h 2014
# Ewa

from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from builtins import range
from DAE import *
import numpy as np
import pylab as pl
import sys
from random import sample
from sklearn import linear_model
from sklearn.linear_model import LogisticRegression
from collections import defaultdict
from collections import namedtuple
import RegionOperations
from GenomicScores import *
from GeneModelFiles import get_gene_regions


# all available now:
# 'nt':'nt'
# 'GC_5':'gc'
# 'GC_10':'gc'
# 'GC_20':'gc'
# 'GC_50':'gc'
# 'GC_100':'gc'
# 'cov-':'cov'
# 'cov/':'cov'

Genomic_scores = {'nt':'nt', 'cov/':'cov', 'GC_5':'gc'} # very important line

genomic_arrays = list(set(Genomic_scores.values()))
scores = list(Genomic_scores.keys())


#outfile = 'scores_per_gene.txt'


print("Loading scores...", file=sys.stderr)

A_dict = {}
all_arrays = []
for s in genomic_arrays:
    gs = load_genomic_scores("/data/unsafe/autism/genomes/hg19/GenomicScores/Other/" + s + ".npz")
    all_arrays.append(gs)
    A_dict[s] = gs


Main_array = create_one_array(*all_arrays)
A = Main_array.array
chrInds = Main_array.index

print("Creating training arrays ...", file=sys.stderr)
#----- Creating arrays: denovo (D), random (R) --------

stds = vDB.get_studies('allWE')   ## DE NOVO STUDIES - A POSSIBLE PARAMETER
locs = [v.location for v in vDB.get_denovo_variants(stds,variantTypes="sub")]

types = []
for s in scores:
    t = A[s].dtype.type
    if t == np.string_:
        t = '<i8'
    types.append((s, t))
D=np.zeros((len(locs), 1), dtype=types).reshape(len(locs))

denovo_inds = []
k = 0
for loc in locs:
    if chr == 'X' or chr == "Y":
        D = np.delete(D,-1,0)
        continue
    chr = loc.split(":")[0]
    loc_index = gs.get_index(loc)
    if loc_index == None:
        sys.stderr.write(chr + ":" + str(pos) + " has not been found\n")
        D = np.delete(D,-1,0)
        continue
    denovo_inds.append(loc_index)
    
    for i in scores:
        ar = A_dict[Genomic_scores[i]]
        sc = ar.Scores[i][chr][loc_index]
        if i == 'nt':
            D[k]['nt'] =  1 if sc in ['G', 'C'] else 0
        else:
           D[k][i] =  sc 
    k += 1

D = np.column_stack([D[s] for s in scores])



nt2N = {'A':0, 'C':1, 'G':1, 'T':0, 'N':0}

AA = np.zeros((len(A),len(scores)))
for i in range(0, len(scores)):
    if scores[i] == "nt":
        for n,nn in list(nt2N.items()):
            AA[A['nt']==n,i] = nn
    else:
        AA[:,i] = A[scores[i]]

S = set(np.arange(len(AA))) - set(denovo_inds)


rand_inds = sample(S,len(D))  # LENGTH OF THE RANDOM ARRAY
R = AA[rand_inds]



#------------ Logistic Regression Classifier ---------
print("Running the logistic regression...", file=sys.stderr)

lrc = linear_model.LogisticRegression()

target = np.concatenate([np.ones((len(D),), dtype=np.int), np.zeros((len(R),), dtype=np.int)])
lrc.fit(np.concatenate([D, R]),target) 
pp = lrc.predict_proba(AA)
pp = np.round(pp, 5)


S = np.core.records.fromarrays([A['chr'], A['pos'], pp[:,0],pp[:,1]], names='chr,pos,pp_0,pp_1')


#------------- Gene Regions -------------------------
print("Calculation the gene regions...", file=sys.stderr)

GMs = genomesDB.get_gene_models()
GeneRgns = get_gene_regions(GMs, autosomes=True)

print("Joining the gene regions with the calculated per-base score...", file=sys.stderr)

#------------ Joining gene regions + classifier scores -----------------

DD = integrate(S, chrInds, GeneRgns, 'pp_1')


# ----------- Writing results to the file ---------------------

#res = open(outfile, 'w')

print("Writing the output...", file=sys.stderr)

print("\t".join("gene score coveredLen totalLen".split()))
for k, v in sorted(list(DD.items()), key = lambda x: x[1]['score'], reverse=True):
    print("\t".join([k, str(v['score']), str(v['length_cov']), str(v['length_total'])]))
    #res.write("\t".join([k, str(v['score']), str(v['length_cov']), str(v['length_total'])]) + "\n")

#res.close()

#sys.stderr.write("File saved as: " + outfile + "\n")
            
        
    
    

