#!/bin/env python

# Jan 6th 2013
# Ewa

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


#genomic_arrays = ['nt', 'cov']
#scores = ['nt', 'cov/']


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
scores = Genomic_scores.keys()

def create_gene_regions():

    goodChr = [str(i) for i in xrange(1,23)]
    
    genes = defaultdict(lambda : defaultdict(list)) 
    GMs = genomesDB.get_gene_models()


    for gm in GMs.transcriptModels.values():
        if gm.chr in goodChr:
            genes[gm.gene][gm.chr] += gm.CDS_regions()

    rgnTpls = []

    for gnm,chrsD in genes.items():
        for chr,rgns in chrsD.items():
        
            clpsRgns = RegionOperations.collapse_noChr(rgns)
            for rgn in sorted(clpsRgns,key=lambda x: x.start):
                rgnTpls.append((int(chr),rgn.start,rgn.stop,gnm))


    geneRgns = [rgnTpl for rgnTpl in sorted(rgnTpls)]

    return(geneRgns)


def join_intervals(D):

    for chr in D.keys():
        prev = (-2,-2)
        for key in sorted(D[chr].keys(), key=lambda tup: tup[0]):
            if key[0] == prev[1] + 1:
                D[chr][(prev[0], key[1])] = (D[chr][prev][0], D[chr][key][1])
                del D[chr][prev]
                del D[chr][key]
                prev = (prev[0], key[1])
            else:
                prev = key

def create_index_binary(Ar, D, k):
    
    posb = Ar[0][1]
    chrb = Ar[0][0]
    pose = Ar[-1][1]
    chre = Ar[-1][0]
    length = len(Ar)
    if chrb == chre and pose - length + 1 == posb:
        D[chrb][(posb, pose)] = (k, k+length-1)
        
    else:
        create_index_binary(Ar[:length/2], D, k)
        create_index_binary(Ar[length/2:], D, k+length/2)

def create_index(Ar):
    
    Inds = defaultdict(dict)
    create_index_binary(Ar, Inds, 0)
    join_intervals(Inds)
    Inds.pop('X')
    Inds.pop('Y')
    return(Inds)
        



def bin_search1(p, I):
    inds = I.keys()
    inds.sort(key=lambda x: int(x[0]))
    b = 0
    e = len(inds)

    while True:
        x = b + (e-b)/2
        if inds[x][1] >= p >=inds[x][0]:
            return(I[inds[x]])
            break
        if p < inds[x][0]:
            e = x-1
        else:
            b = x+1
        if b > e:
            return(None)

outfile = 'scores_per_gene.txt'


print >>sys.stderr, "Loading scores..."

A_dict = {}
all_arrays = []
for s in genomic_arrays:
    gs = load_genomic_scores("/data/unsafe/autism/genomes/hg19/GenomicScores/Other/" + s + ".npz")
    all_arrays.append(gs)
    A_dict[s] = gs


Main_array = create_one_array(*all_arrays)
A = Main_array.array
chrInds = Main_array.index

print >>sys.stderr, "Creating training arrays ..."
#----- Creating arrays: denovo (D), random (R) --------

stds = vDB.get_studies('allWE')
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
for i in xrange(0, len(scores)):
    if scores[i] == "nt":
        for n,nn in nt2N.items():
            AA[A['nt']==n,i] = nn
    else:
        AA[:,i] = A[scores[i]]

S = set(np.arange(len(AA))) - set(denovo_inds)


rand_inds = sample(S,len(D))  # LENGTH OF THE RANDOM ARRAY
R = AA[rand_inds]



#------------ Logistic Regression Classifier ---------
print >>sys.stderr, "Running the logistic regression..."

lrc = linear_model.LogisticRegression()

target = np.concatenate([np.ones((len(D),), dtype=np.int), np.zeros((len(R),), dtype=np.int)])
lrc.fit(np.concatenate([D, R]),target) 
pp = lrc.predict_proba(AA)
pp = np.round(pp, 5)


S = np.core.records.fromarrays([A['chr'], A['pos'], pp[:,0],pp[:,1]], names='chr,pos,pp_0,pp_1')


#------------- Gene Regions -------------------------
print >>sys.stderr, "Calculation the gene regions..."

GeneRgns = create_gene_regions()

print >>sys.stderr, "Joining the gene regions with the calculated per-base score..."

#------------ Joining gene regions + classifier scores -----------------

DD = integrate(S, chrInds, GeneRgns, 'pp_1')

# ----------- Writing results to the file ---------------------

#res = open(outfile, 'w')

print >>sys.stderr, "Writing the output..."


for k, v in sorted(DD.items(), key = lambda x: x[1]['score'], reverse=True):
    print("\t".join([k, str(v['score']), str(v['length_cov']), str(v['length_total'])]))
    #res.write("\t".join([k, str(v['score']), str(v['length_cov']), str(v['length_total'])]) + "\n")

#res.close()

#sys.stderr.write("File saved as: " + outfile + "\n")
            
        
    
    

