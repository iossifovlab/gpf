#!/bin/env python

import sys


def isSorted(F,fmt,faiFN="/data/unsafe/autism/genomes/GATK_ResourceBundle_5777_b37_phiX174/chrAll.fa.fai",printError=False):
    chrInd = {}

    FAIF = open(faiFN)
    chrInd = { ln.split("\t")[0]:li  for li,ln in enumerate(FAIF) }
    FAIF.close()


    hdL = F.readline()
    hdCs = hdL.split("\t")

    if fmt=="dnv":
        try:
            locCI = hdCs.index("location")
            varCI = hdCs.index("variant")
        except ValueError:
            return 2 

        prevKey = (-1,-1,"aaaaa")   
        for l in F: 
            if l[0] == "#":
                continue
            cs = l.strip().split('\t')
            ch,pos = cs[locCI].split(":")
            try:
                pos = int(pos)
            except ValueError:
                return 2
            if ch not in chrInd:
                continue
            chI = chrInd[ch]
            vr = cs[varCI]
            key = (chI,pos,vr)

            if key < prevKey:
                if printError:
                    print prevKey, key
                return 1
            prevKey = key

    elif fmt=="trm":
        try:
            chrCI = hdCs.index("chr")
            posCI = hdCs.index("position")
            varCI = hdCs.index("variant")
        except ValueError:
            return 2 
       
        prevKey = (-1,-1,"aaaaa")   
        for l in F: 
            if l[0] == "#":
                continue
            cs = l.strip().split('\t')
            ch = cs[chrCI]
            if ch not in chrInd:
                continue
            pos = int(cs[posCI])
            chI = chrInd[ch]
            vr = cs[varCI]
            key = (chI,pos,vr)

            if key < prevKey:
                if printError:
                    print prevKey, key
                return 1
            prevKey = key

    else:
        print >>sys.stderr, "Unknown format", fmt
        assert False
        return 3

    return 0

if __name__ == "__main__":
    fmt = "dnv"
    if len(sys.argv) > 1:
        fmt = sys.argv[1]

    faiFN = "/data/unsafe/autism/genomes/GATK_ResourceBundle_5777_b37_phiX174/chrAll.fa.fai"
    if len(sys.argv) > 2:
        faiFN = sys.argv[2]

    sys.exit(isSorted(sys.stdin,fmt,faiFN,printError=True))
