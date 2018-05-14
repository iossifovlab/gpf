#!/bin/env python

from __future__ import print_function
import sys
from DAE import *
from collections import defaultdict
from pylab import *
import scipy.stats
from math import log10

if len(sys.argv) < 2:
    sys.stderr.write("\nTHE SCRIPT REQUIRES A PARAMETER: input file name\n\n")
    sys.exit(-1)


N = 8 # how many parts


file = open(sys.argv[1])
S = [l.split() for l in file]
file.close()
total_Score = sum([float(x[1]) for x in S])

total_length_cov = sum([float(x[2]) for x in S])

stds = vDB.get_studies('allWE')
locs = [v.geneEffect for v in vDB.get_denovo_variants(stds,variantTypes="sub")]
denovo_cnt = len(locs)
G = defaultdict(int)
for l in locs:
    if l != []:
        G[l[0]['sym']] += 1



part_size = len(S)/N

# FANCY SCORE
Obs = []
Exp_fs = []
Exp_len = []
#print("obs", "exp_fs", "exp_len")
for i in xrange(part_size, len(S), part_size):
    exp_fs =  denovo_cnt*(float(sum([float(x[1]) for x in S[i - part_size : i]]))/total_Score)
    exp_len = denovo_cnt*(float(sum([float(x[2]) for x in S[i - part_size : i]]))/total_length_cov)
    Exp_fs.append(exp_fs)
    Exp_len.append(exp_len)
    obs = float(sum([G[g[0]] for g in S[i - part_size : i] if  G[g[0]]]))
    Obs.append(obs)
    #print(obs, exp_fs, exp_len)
    

#chi2_fs = sum([ ((o-e)**2)/e for o, e in zip(Obs, Exp_fs)])
#print chi2_fs
chi2_fs = scipy.stats.chisquare(np.array(Obs), np.array(Exp_fs))
print("FANCY SCORE: chi2-stat: " + str(chi2_fs[0]) + " p-val: " + "%e" % chi2_fs[1]) 
chi2_len = scipy.stats.chisquare(np.array(Obs), np.array(Exp_len))
print("LENGTH: chi2-stat: " + str(chi2_len[0]) + " p-val: " + "%e" %  chi2_len[1])
#chi2_len = sum([ ((o-e)**2)/e for o, e in zip(Obs, Exp_len)])
#degrees_of_freedom = part_size*2



plot(Exp_fs, Obs, 'ro', color='red')
xlabel("EXPECTED RATE")
ylabel("OBSERVED RATE")
plot(Exp_len, Obs, 'ro', color='green')
max_el = max(max(Exp_fs), max(Obs), max(Exp_len))
plot((0,max_el),(0,max_el), color='black')
legend(("fancy score", "length"), 'upper left')
show()

