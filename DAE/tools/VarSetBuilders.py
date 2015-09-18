#!/bin/env python

from pylab import *
from collections import defaultdict
from DAE import *
import VariantAnnotation
import sys,re,subprocess

_nts = set("ACGT")
_ntRe = re.compile("^[ACGT]+$")

def vcf2CshlVar(chr,pos,refA,altA):
    if refA in _nts and altA in _nts:
        variant = "sub(" + refA + "->" + altA + ")"
        location = chr + ":" + str(pos)
    elif _ntRe.match(refA) and _ntRe.match(altA):
        if refA.startswith(altA):
            variant = "del(" + str(len(refA)-len(altA)) + ")"
            location = chr + ":" + str(pos+1)
        elif altA.startswith(refA):
            variant = "ins(" + altA[len(refA):] + ")"
            location = chr + ":" + str(pos+1)
        else:
            raise Exception("OOOOOOOOOOO")
    else:
        raise Exception("PPPP")
    return variant,location


class VarSet:
    def __init__(self,families):
        self.families = families
        self.pids = {pd.personId:(fd.familyId,pInd) 
                                for fd in self.families.values() 
                                    for pInd,pd in enumerate(fd.memberInOrder) }
        self.fmVars = {}
        self.allAttsS = set()
                
    def addPersonCshlVar(self,personId,loc,var,atts):
        # if personId not in self.pids:
        #     print "MALE", personId
        #     return 
        fmId,pInd = self.pids[personId]
        kk = (fmId,loc,var)
        if kk not in self.fmVars:
            fd = self.families[fmId]

            class FMVar:
                pass

            fmVr = FMVar()
            fmVr.fmId = fmId
            fmVr.loc = loc
            fmVr.var = var

            fmVr.bsSt = zeros((2,len(fd.memberInOrder)),dtype=int)
            for c in xrange(len(fd.memberInOrder)):
                fmVr.bsSt[0,c] = normalRefCopyNumber(loc,fd.memberInOrder[c].gender)

            self.fmVars[kk] = fmVr
        self.fmVars[kk].atts = atts
        self.fmVars[kk].bsSt[0,pInd] -= 1
        self.fmVars[kk].bsSt[1,pInd] += 1

        self.allAttsS |= set(atts.keys())

    def addPersonVCFVar(self,personId,chr,pos,refA,altA,atts):
        var,loc = vcf2CshlVar(chr,pos,refA,altA)
        self.addPersonCshlVar(personId,loc,var,atts)

    def save(self,fn):
        GA = genomesDB.get_genome()
        gmDB = genomesDB.get_gene_models()
 
        allAtts = sorted(self.allAttsS)
        chrOrd = {ch:chI for chI,ch in enumerate(GA.allChromosomes)}

        noAnnotFn = fn + ".noAnnot"
        OF = open(noAnnotFn,"w")
        hcs = "familyId location variant bestState inChild effectType effectGene effectDetails".split() + allAtts
        OF.write("\t".join(hcs) + "\n")
        for v in sorted(self.fmVars.values(),key=lambda x: (chrOrd[x.loc.split(":")[0]],int(x.loc.split(":")[1]),x.var)):
            effects = VariantAnnotation.annotate_variant(gmDB, GA, var=v.var, loc=v.loc)
            desc = VariantAnnotation.effect_description(effects)

            mbrs = self.families[v.fmId].memberInOrder
            childStr = ''
            for c in xrange(2,len(mbrs)):
                if isVariant(v.bsSt,c,v.loc,mbrs[c].gender):
                    childStr += (mbrs[c].role + mbrs[c].gender)
 
            cs = [v.fmId,v.loc,v.var,mat2Str(v.bsSt),childStr] + list(desc) + [v.atts[a] if a in v.atts else "" for a in allAtts]
            OF.write("\t".join(cs) + "\n")
        OF.close()
        ev = subprocess.call("annotateFreqTransm.py %s > %s" % (noAnnotFn,fn),shell=True)
        if ev!=0:
            raise "annotateFreqTransm.py failed"
        subprocess.call("rm %s" % (noAnnotFn),shell=True)
    
