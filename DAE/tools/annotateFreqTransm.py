#!/bin/env python

import gzip
from heapq import heappush,heappop
import pysam
import os
import sys
from DAE import *

# tF = "/home/iossifov/work/T115/data-dev/bbbb/w1202s766e611/transmissionIndex-HW-DNRM.txt.bgz"
fF = "/home/iossifov/work/T115/data-dev/bbbb/EVS/EVS.format.Both.txt.bgz"

# tF = "/home/iossifov/work/T115/data-dev/study/w1202s766e611/transmissionIndex-HW-DNRM.txt.bgz"
# fF = "/home/iossifov/work/T115/data-dev/study/EVS/EVS.format.Both.txt.bgz"

class BlockFile:
    def __init__(bf,fl):
        bf.fl = fl 
        bf.hdrL = bf.fl.readline()

        hdrCs = bf.hdrL.strip().split("\t")
        bf.locationInd = -1
        bf.chrInd = -1
        bf.posInd = -1

        try:
            bf.locationInd = hdrCs.index("location")
        except ValueError:
            bf.chrInd = hdrCs.index("chr") 
            bf.posInd = hdrCs.index("position") 
        
        bf._chMap = {"X":23, "Y":24}
        for chN in xrange(1,23):
            bf._chMap[str(chN)] = chN    

        bf._nextLine()
        bf.key = (0,0)
        bf.nextBlock()

    def line2K(bf,lncs):
        if bf.locationInd > 0:
            ch,pos = lncs[bf.locationInd].split(":")
            pos = int(pos)
        else:
            ch = lncs[bf.chrInd]
            pos = int(lncs[bf.posInd])

        try:
            chN = bf._chMap[ch]
        except KeyError:
            chN = 100 
        return (chN,pos)
    

    def _nextLine(bf):
        ln = bf.fl.readline()
        while ln and ln[0] == '#':
            ln = bf.fl.readline()
        if ln:
            bf.nextLine = ln.strip().split('\t')
        else:
            bf.nextLine = None
        
    def nextBlock(bf):
        bf.block = []
        if not bf.nextLine:
            bf.key = None
            return False

        prevKey = bf.key
        bf.key = bf.line2K(bf.nextLine)
        assert bf.key > prevKey

        while bf.nextLine and bf.line2K(bf.nextLine) == bf.key:
            bf.block.append(bf.nextLine)
            bf._nextLine()
        return True
        

class JoinFiles:
    def __init__(self,bfFiles):
        self.bfFiles = bfFiles 
        self.hp = []

        for bfI,bf in enumerate(self.bfFiles):
            if bf.key:
                heappush(self.hp,((bf.key,bfI)))

    def next(self):
        if len(self.hp)==0:
            return False 

        r = [None for x in self.bfFiles]
        k  = self.hp[0][0]
        while self.hp and self.hp[0][0] == k:
            tk,bfI = heappop(self.hp)
            bf = self.bfFiles[bfI]
            r[bfI] = bf.block
            bf.nextBlock()
            if bf.key:
                heappush(self.hp,((bf.key,bfI)))
        self.k = k 
        self.rs = r
        return True
           

chrInd = {}
faiFN="/data/unsafe/autism/genomes/GATK_ResourceBundle_5777_b37_phiX174/chrAll.fa.fai"
FAIF = open(faiFN)
chrName = [ ln.split("\t")[0]  for ln in FAIF ]
FAIF.close()
chrInd = { chN:chI  for chI,chN in enumerate(chrName) }

 
class TMFile:
    def __init__(self,fN):
        self.fN = fN
        self.F = gzip.open(self.fN, 'rb')
        self.hdrL = self.F.readline().strip()
        self.hdrCs = self.hdrL.split("\t")
    
        self.chrCI = self.hdrCs.index("chr")
        self.posCI = self.hdrCs.index("position")
        self.varCI = self.hdrCs.index("variant")

    def lines(self):
        for ln in self.F:
            if ln[0] == '#':
                continue 
            cs = ln.strip("\n\r").split('\t')

            ch = cs[self.chrCI]
            pos = int(cs[self.posCI])
            chI = chrInd[ch]
            vr = cs[self.varCI]
            key = (chI,pos,vr)

            yield (key,cs)

    def close(self):
        self.F.close()


class DNVFile:
    def __init__(self,fN):
        self.fN = fN
        self.F = open(self.fN)
        self.hdrL = self.F.readline().strip()
        self.hdrCs = self.hdrL.split("\t")

        self.locCI = self.hdrCs.index("location")
        self.varCI = self.hdrCs.index("variant")
    

    def lines(self):
        for ln in self.F:
            if ln[0] == '#':
                continue 
            cs = ln.strip("\n\r").split('\t')

            ch,pos = cs[self.locCI].split(":")
            pos = int(pos)
            chI = chrInd[ch]
            vr = cs[self.varCI]
            key = (chI,pos,vr)

            yield (key,cs)
    


    def close(self):
        self.F.close()

       
def openFile(fN):
    if fN.endswith(".txt.bgz"):
        return TMFile(fN)
    else:
        return DNVFile(fN)

class IterativeAccess:
    def __init__(self,fN,clmnN):
        self.fN = fN
        self.clmnN = clmnN 
        self.tmf =  TMFile(fN)
        self.tmfLines = self.tmf.lines() 
        self.clmnI = self.tmf.hdrCs.index(self.clmnN)
        self.currKey = (-1,0,0)

    def getV(self,k):
        if self.currKey < k:
            for self.currKey,self.currCs in self.tmfLines:
                if self.currKey >= k:
                    break
            if self.currKey < k:
                self.currKey = (100000,0,0)

        if self.currKey == k:
            return self.currCs[self.clmnI]
        return 

    def close(self):
        self.tmf.close() 
                

class DirectAccess:
    def __init__(self,fN,clmnN):
        self.fN = fN
        self.clmnN = clmnN 
        tmf =  TMFile(fN)
        self.clmnI = tmf.hdrCs.index(self.clmnN)
        self.varI = tmf.varCI
        tmf.close()
        self.F = pysam.Tabixfile(self.fN)

    def getV(self,k):
        chI,pos,vr = k
        ch = chrName[chI]


        try:
            for l in self.F.fetch(ch, pos-1, pos):
                cs = l.strip("\n\r").split("\t")
                if vr != cs[self.varI]:
                    continue
                return cs[self.clmnI]
        except ValueError:
            pass 
        return 
        
    def close(self):
        self.F.close() 

if __name__ == "__old_main__":

    fClmN = "all.altFreq"
    tClmN = "gosho"

    DAF = DirectAccess(fF,fClmN)
    IAF = IterativeAccess(fF,fClmN)

    FF = openFile(fF)
    FT = openFile(tF)

    fClmNI = FF.hdrCs.index(fClmN)

    FFI = FF.lines()

    fk = (-1, 0, 0)

    for tk,tcs in FT.lines():
        if fk<tk:
            for fk,fcs in FFI:
                if fk>=tk:
                    break
            if fk<tk:
                ffk = (100000,0,0)


        v = 'gosho'
        if fk==tk:
            v = fcs[fClmNI]

        daV = DAF.getV(tk)
        iaV = IAF.getV(tk)

        tcs.append(fcs[fClmNI])
        print tk,v,daV,iaV

        if v != daV:
            x10
        if v != iaV:
            x10
        
    FT.close()
    FF.close()
    

    ''' 
    bfs = [BlockFile(F1), BlockFile(F2)]

    jf = JoinFiles(bfs)
    while jf.next():
        if jf.rs[0] and jf.rs[1]:
            print jf.k 
            print "\t0:",jf.rs[0]
            print "\t1:",jf.rs[1]
    '''

if __name__ == "__main__":
    tFN = "/home/iossifov/work/T115/data-dev/bbbb/IossifovWE2014/Supplement-T2-eventsTable-annot.txt"
    if len(sys.argv) > 1:
        tFN = sys.argv[1]

    accessMode = "direct"
    if len(sys.argv) > 2:
        accessMode = sys.argv[2]

    freqAttFN = vDB._config.get("DEFAULT","wd") + "/freqAtts.txt" 
    if len(sys.argv) > 3:
        freqAttFN = sys.argv[3]


    modeConstructor = {"direct": DirectAccess, "iterative":IterativeAccess} 

    tF = openFile(tFN)

    outHdr = list(tF.hdrCs)
    freqAttF = open(freqAttFN)

    fFS = []
    for l in freqAttF:
        ffN,tAN,fAT = l.strip().split("\t")
        try:
            tANI = tF.hdrCs.index(tAN)
        except ValueError:
            tANI = -1
            outHdr.append(tAN)
        
        AF = modeConstructor[accessMode](vDB._config.get("DEFAULT","studyDir") + "/" + ffN,fAT)
        fFS.append((AF,tANI))

    print "\t".join(outHdr)
    for tk,tcs in tF.lines():
        for AF,tANI in fFS:
            v = AF.getV(tk) 
            if not v:
                v = ""
            if tANI == -1:
                tcs.append(v)
            else:
                tcs[tANI] = v
        print "\t".join(tcs)
