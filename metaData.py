#!/bin/env python
from __future__ import print_function
from collections import defaultdict
import sys

def loadTable(fn):
    rows = []
    f = open(fn)
    hdr = f.readline().strip().split(",")[1:]
  
    for l in f:
        if not l.startswith("RR,"):
           continue
        cs = l.strip().split(",")
        rows.append(dict(zip(hdr,cs[1:])))
    return rows

class MetaData:
    def __init__(self,dir):
        self.SM = {}
        self.BC = {}
        self.LB = {}
        self.CP = {}
        self.LN = {}

        self.SQ = {}
        self.SQbyFc = {}

        self._gndrs = "M F".split() 
        self._roles = "mother father self sibling invalid proband-twin p2 s2 s3 s4 s5 x1 proband".split() 
        self._lbTypes = "PE SE".split() 
        self._srTypes = "PE SE".split() 
        self._load(dir)

    def _load(self,dir):
        for r in loadTable(dir + "/sample.csv"):
            self.addSm(r['sample_id'], r['person_id'],r['sample_type'], \
                        r['FamilyId'],r['Gender'], r['RelationToProband'], r)

        for r in loadTable(dir + "/barcode.csv"):
            self.addBc(r['barcode_id'],r['sequence'],r)

        for r in loadTable(dir + "/library.csv"):
            if r['barcode_id'] == '\N':
                self.addLb(r['library_id'], r['sample_id'],None,r['pe_or_se'],r)
            else:
                self.addLb(r['library_id'], r['sample_id'],r['barcode_id'],r['pe_or_se'],r)
        for r in loadTable(dir + "/capture.csv"):
            self.addCp(r['capture_id'],r['chip_id'],r)

        for r in loadTable(dir + "/library_capture_rel.csv"):
            self.addLbToCp(r['library_id'],r['capture_id'])

        for r in loadTable(dir + "/seqrun.csv"):
            self.addSr(r['seqrun_id'],r['pe_or_se'],r['fc'],r['read_length'],r['run_date'],r)
        for r in loadTable(dir + "/lane.csv"):
            self.addLn(r['fc'],r['lane'],r['capture_id'],r)

    def addLn(self,fc,number,captureId,atts): 
        laneId = fc + "-" + number
        if laneId in self.LN:
            raise Exception("duplicated lane id " + laneId)
        class LN:
            pass
        ln = LN()
        ln.fc = fc
        ln.number = number 
        if fc in self.SQbyFc:
            ln.seqrun = self.SQbyFc[fc]
        else:
            ln.seqrun = None
            print("The fc ", fc, "has not sequencing run", file=sys.stderr)
        ln.capture = self.CP[captureId]
        ln.capture.lanes.append(ln)
        ln.atts = atts

        self.LN[laneId] = ln
    
    def addSr(self,seqrunId,type,fc,readLength,dateS,atts):
        if seqrunId in self.SQ:
            raise Exception("duplicated seqrunid " + seqrunId)
        if fc in self.SQbyFc:
            raise Exception("duplicated flowcell " + fc)
        class SR:
            pass
        sr = SR()
        sr.seqrunId = seqrunId
        sr.type = type
        if sr.type not in self._srTypes:
            raise Exception("Unknown sequencing run type: " . sr.type)
        sr.fc = fc
        sr.readLength = readLength
        sr.dateS = dateS
        sr.atts = atts

        self.SQ[sr.seqrunId] = sr
        self.SQbyFc[sr.fc] = sr

    def addLbToCp(self,libraryId,captureId):
        lb = self.LB[libraryId]
        cp = self.CP[captureId]

        if libraryId in [l.libraryId for l in cp.libraries]:
            raise Exception("The library " + libraryId + " can not be added twice to the campture " + captureId)

        cp.libraries.append(lb)
        lb.captures.append(cp)
        
    def addCp(self,captureId,chipId,atts=None):
        if captureId in self.CP:
            raise Exception("duplicated capture id" + captureId)
        class CP:
            pass
        cp = CP()
        cp.captureId = captureId
        cp.chipId = chipId
        cp.libraries = []
        cp.lanes = []
        cp.atts = atts
        self.CP[cp.captureId] = cp
        
        
    def addLb(self,libraryId,sampleId,barcodeId,type,atts=None):
        if libraryId in self.LB:
            raise Exception("duplicated library id" + libraryId)

        class LB:
            pass
        lb = LB()
        lb.libraryId = libraryId

        sm = self.SM[sampleId]
        lb.sample = sm
        sm.libraries.append(lb)

        if barcodeId:
            lb.barcode = self.BC[barcodeId] 
        else:
            lb.barcode = None
        lb.type = type

        if lb.type not in self._lbTypes:
            raise Exception("Unknown library type: " . lb.type)
        lb.captures = [] 
        lb.atts = atts
        self.LB[libraryId] = lb

    def addBc(self,barcodeId,sequence,atts=None):
        if barcodeId in self.BC:
            raise Exception("duplicatd barcode id" + barcodeId)
        class BC:
            pass
        bc = BC()
        bc.barcodeId = barcodeId
        bc.sequence = sequence
        bc.atts = atts
        self.BC[bc.barcodeId] = bc

    def addSm(self,sampleId,personId,sampleType,familyId,gender,relationToProband,atts=None):
        if sampleId in self.SM:
            raise Exception("duplicated sample id " + sampleId)

        class SM:
            pass
        sm = SM()
        sm.sampleId = sampleId
        sm.personId = personId
        sm.sampleType = sampleType 
        sm.familyId = familyId 
        sm.gender = gender
        sm.relationToProband = relationToProband 
        sm.libraries = []
        sm.atts = atts

        if sm.gender not in self._gndrs:
            raise Exception("worng sample gender: " + sm.gender)
        if sm.relationToProband not in self._roles:
            raise Exception("worng sample relation to proband: " + sm.relationToProband)

        self.SM[sm.sampleId] = sm

if __name__ == "__main__":
    print('hi')

    md = MetaData('/home/iossifov/work/T115/filesReport/metaData_STATE')
    '''
    LC = loadTable('/data/safe/autism/pilot2_STATELAB/metaData/library_capture_rel.csv')
    LB = loadTable('/data/safe/autism/pilot2_STATELAB/metaData/library.csv')

    lbb = {lbr['library_id']:lbr['barcode_id'] for lbr in LB}
    cbs = defaultdict(list)

    for lcr in LC:
        cbs[lcr['capture_id']].append(lbb[lcr['library_id']])

    '''
