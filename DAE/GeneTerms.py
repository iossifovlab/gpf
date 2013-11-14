#!/bin/env python

from collections import defaultdict
import glob
import os

class GeneTerms:
    def __init__(self):
        self.g2T = defaultdict(lambda : defaultdict(int)) 
        self.t2G = defaultdict(lambda : defaultdict(int)) 
        self.tDesc = {}
        self.geneNS = None

    def renameGenes(self, geneNS, renameF):
        g2T = self.g2T
        self.g2T = defaultdict(lambda : defaultdict(int))
        self.t2G = defaultdict(lambda : defaultdict(int))
        for g,ts in g2T.items():
            ng = renameF(g)
            if ng:
                self.g2T[ng] = ts
        for g,ts in self.g2T.items():
            for t, n in ts.items():
                self.t2G[t][g] = n
        for t in set(self.tDesc)-set(self.t2G):
            del self.tDesc[t]
        self.geneNS = geneNS

    def save(self,fn):
        if fn.endswith("-map.txt"):
            mapFn = fn
            dscFn = fn[:-4] + "names.txt"
        else:
            mapFn = fn + "-map.txt"
            dscFn = fn + "-mapnames.txt"

        mapF = open(mapFn,'w')
        mapF.write("#geneNS\t" + self.geneNS + "\n")
        for g in sorted(self.g2T):
            ts = []
            for t,tn in sorted(self.g2T[g].items()):
                ts += [t]*tn
            mapF.write(g + "\t" + " ".join(ts) + "\n")
        mapF.close()

        dscFn = open(dscFn,'w')
        dscFn.write("\n".join([t + "\t" + dsc for t, dsc in sorted(self.tDesc.items())]) + "\n")
        dscFn.close()


def _ReadEwaSetFile(inputDir):
    r = GeneTerms()
    r.geneNS = "sym"
    for sf in glob.glob(inputDir + "/*.txt"):
        p, fn = os.path.split(sf)
        setname,ex = os.path.splitext(fn)
        f = open(sf,'r')
        r.tDesc[setname] = f.readline().strip()
        for line in f:
            gSym = line.strip()
            r.t2G[setname][gSym]+=1
            r.g2T[gSym][setname]+=1
        f.close()
    return r


def _ReadMappingFile(inputFile):
    r = GeneTerms()
    r.geneNS = "id"
    f = open(inputFile)
    for ln in f:
        line = ln.strip().split()
        if line[0]=='#geneNS':
            r.geneNS = line[1]
            continue
        geneId = line[0]
        del line[0]
        for t in line:
            r.t2G[t][geneId]+=1
            r.g2T[geneId][t]+=1
    f.close()
    nmsFl = inputFile[:-4] + "names.txt"
    try :
        nf = open(nmsFl)
        for line in nf:
            (t,desc) = line.strip().split("\t",1)
            if t in r.t2G:
                r.tDesc[t] = desc
    except IOError:
        pass
    for t in set(r.t2G)-set(r.tDesc):
        r.tDesc[t] = ""
    return r
        
def loadGeneTerm(path):
    if path.endswith("-map.txt"):
        return _ReadMappingFile(path)
    else:
        return _ReadEwaSetFile(path)

if __name__ == "__main__":
    print "hi"
    # gt = loadGeneTerm('/mnt/wigclust5/data/unsafe/autism/genomes/hg19/miRNA-TargetScan6.0-Conserved')
    gt = loadGeneTerm('/data/safe/ecicek/Workspace6/GeneToTermMapping/Domain-map.txt')

