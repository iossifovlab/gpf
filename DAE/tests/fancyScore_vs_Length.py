#!/bin/env python

import sys
from DAE import *
from collections import defaultdict
from pylab import *

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
print("obs", "exp_fs", "exp_len")
for i in xrange(part_size, len(S), part_size):
    exp_fs =  float(sum([float(x[1]) for x in S[i - part_size : i]]))/total_Score
    exp_len = float(sum([float(x[2]) for x in S[i - part_size : i]]))/total_length_cov
    Exp_fs.append(exp_fs)
    Exp_len.append(exp_len)
    obs = float(sum([G[g[0]] for g in S[i - part_size : i] if  G[g[0]]]))/denovo_cnt
    Obs.append(obs)
    print(obs, exp_fs, exp_len)
    

plot(Exp_fs, Obs, 'ro', color='red')
xlabel("EXPECTED RATE")
ylabel("OBSERVED RATE")
plot(Exp_len, Obs, 'ro', color='green')
plot((0,1),(0,1), color='black')
legend(("fancy score", "length"), 'upper left')
show()

