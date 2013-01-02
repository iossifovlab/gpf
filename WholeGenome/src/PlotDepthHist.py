#/data/software/local/bin/python

# filename : 
# generated : 
# author(s) : 
# origin : CSHL
# purpose : 
# caveates: 

import numpy as np
import matplotlib.pyplot as plt

outPath = "/data/safe/leotta/sge/DepthCoverage/"
families = ['auSSC12596','auSSC12605']

chroms = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22]

for family in families:
    for chrom in chroms:
        filename = "%s%s/%s-%s-Depths-Histogram.txt"%(outPath,family,family, chrom)
        figName = "%s%s/%s-%s-Depths-Histogram.png"%(outPath,family,family, chrom)
        plotTitle = "Family %s \nChrom %s \nDepth of Coverage Histogram"%(family, chrom)
        
        ar = np.loadtxt(filename)

        plots = []
        fig = plt.figure(1, figsize=(8, 10))   # <---
        for c in range(4):
            p = plt.plot(ar[1:,c])
            plt.xlabel("Coverage")
            plt.ylabel("Base Pairs")
            plots.append(p)
                    
        plt.title(plotTitle)
        plt.xlabel('Coverage')
        plt.ylabel('Base Pairs')                    
        plt.legend(plots, ["Mother", "Father", "Sibling", "Proband"])            
        plt.savefig(figName)
        plt.clf()
        