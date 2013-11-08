#!/bin/env python

# Nov 7th 2013
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

def create_gene_regions():

    goodChr = ["chr" + str(i) for i in xrange(1,23)]
    
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
                rgnTpls.append((int(chr[3:]),rgn.start,rgn.stop,gnm))


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
            e = x
        else:
            b = x
        if b + 1 >= e:
            return(None)

outfile = 'scores_per_gene.txt'

#----- Creating arrays: denovo (D), random (R) --------

A = np.load("/mnt/wigclust5/data/safe/egrabows/2013/MutationProbability/Arrays/chrAll.npy")

chrInds = create_index(A)

stds = vDB.get_studies('allWE')
locs = [v.location for v in vDB.get_denovo_variants(stds,variantTypes="sub")]

D=np.zeros((len(locs), 1), dtype=[('nt', '<i8'),('cov/', '<f8')]).reshape(len(locs))

denovo_inds = []
k = 0
for loc in locs:
    chr, pos = loc.split(":")
    if chr == 'X' or chr == "Y":
        D = np.delete(D,-1,0)
        continue
    pos = int(pos)
    rangeA = bin_search1(pos, chrInds[chr])
    
    if rangeA == None:
        sys.stderr.write(chr + ":" + str(pos) + " has not been found\n")
        D = np.delete(D,-1,0)
        continue

    posS = A[rangeA[0],]['pos']
    ind = rangeA[0] - posS + pos
    hit = A[ind,]
    denovo_inds.append(ind)
    D[k]['nt'] =  1 if hit['nt'] in ['G', 'C'] else 0
    D[k]['cov/'] =  hit['cov/']
    k += 1
D = np.c_[D['nt'], D['cov/']]


nt2N = {'A':0, 'C':1, 'G':1, 'T':0, 'N':0}
AA = np.zeros((len(A),2))
AA[:,1] = A['cov/']
for n,nn in nt2N.items():
    AA[A['nt']==n,0] = nn


S = set(np.arange(len(AA))) - set(denovo_inds)


rand_inds = sample(S,len(D))  # LENGTH OF THE RANDOM ARRAY
R = AA[rand_inds]



#------------ Logistic Regression Classifier ---------

lrc = linear_model.LogisticRegression()

target = np.concatenate([np.ones((len(D),), dtype=np.int), np.zeros((len(R),), dtype=np.int)])
lrc.fit(np.concatenate([D, R]),target) 
pp = lrc.predict_proba(AA)
pp = np.round(pp, 5)


S = np.core.records.fromarrays([A['chr'], A['pos'], pp[:,0],pp[:,1]], names='chr,pos,pp_0,pp_1')


#------------- Gene Regions -------------------------

GeneRgns = create_gene_regions()


#------------ Joining gene regions + classifier scores -----------------
DD = defaultdict(lambda : defaultdict(int))


p = 0
I = sorted(chrInds['1'].keys())
length = len(I)
chr_prev = '1'
for l in GeneRgns:
    chr = str(l[0])
    if chr != chr_prev:
        I = sorted(chrInds[chr].keys())
        chr_prev = chr
        length = len(I)
        p = 0
        
    ex_b = l[1]
    ex_e = l[2]
    pointer = p


    while pointer < length and I[pointer][1] < ex_b:
        pointer += 1
    p = pointer

   
    
    DD[l[3]]['length_total'] += ex_e - ex_b + 1
    
    while pointer < length and I[pointer][0] <= ex_e:

        indexes = chrInds[chr][I[pointer]]
        if ex_b <= I[pointer][0]:
            begin = indexes[0]
        else:
            begin = indexes[0] + ex_b - I[pointer][0]
        
        if ex_e >= I[pointer][1]:
            end = indexes[-1]
        else:
            end = indexes[-1] + ex_e - I[pointer][1] 
        


        DD[l[3]]['score'] += sum(S[begin:end+1]['pp_1'])
        DD[l[3]]['length_cov'] += end - begin + 1
        

        pointer += 1

# ----------- Writing results to the file ---------------------

#res = open(outfile, 'w')


for k, v in sorted(DD.items(), key = lambda x: x[1]['score'], reverse=True):
    print("\t".join([k, str(v['score']), str(v['length_cov']), str(v['length_total'])]))
    #res.write("\t".join([k, str(v['score']), str(v['length_cov']), str(v['length_total'])]) + "\n")

#res.close()

#sys.stderr.write("File saved as: " + outfile + "\n")
            
        
    
    

