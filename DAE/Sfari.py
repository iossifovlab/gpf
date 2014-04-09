#!/bin/env python

import os
import sys 
from collections import defaultdict
import ConfigParser

class Person:
    pass

class Sample:
    pass

class TwinGroup:
    pass

class SfariCollection:
    
    def __init__(self, sfariDir):
        
        self.sfariDir = sfariDir
        self.individual = {}
        self.sample = {}
        self.twinGroups = set() 
        self.familyCenter = {}
        self.familyAgeAtAssement = {}
        
        self._loadIndividual()
        self._loadSample()
        self._loadTwins()
        self._loadCollectionCenter()

# family,id(),sex,father,mother,birth,guid,individual_properties.role,individual_properties.genetic_ab,individual_properties.genetic_ab_notes,family.collection

    def _loadSample(self):
        f = open(os.path.join(self.sfariDir,'RUCDR_ID-Portal_ID-Map_20111130-id.csv'))
        h = f.readline()
        sN2Pid = defaultdict(set) 
        for l in f:
            if l.startswith("#"):
                continue
            cs = l.strip().split(",")
            if len(cs) != 3:
                raise Exception('bbb')

            s = Sample()
            (s.personId,
             s.sampleNumber,
             s.sampleType) = cs 
            # 10001.p1.wb-dna-SSC12345
            s.sampleId = s.personId + "." + s.sampleType + "-" + s.sampleNumber

            if s.sampleId in self.sample:
                raise Exception('sample ' + s.sampleId + ' is defined twice')
            self.sample[s.sampleId] = s
            sN2Pid[s.sampleNumber].add(s.personId)
        self.sampleNumber2PersonId = {}
        for sn, pids in sN2Pid.items():
            if len(pids)!=1:
                raise Exception("SSSSSSSSS")
            self.sampleNumber2PersonId[sn] = iter(pids).next();
           

    def _loadTwins(self):
        f = open(os.path.join(self.sfariDir,'SSC_and_STC_Twins.csv'))
        h = f.readline()
        # Family,Proband Code,Twin Code,Twin Study Role,Zygosity,Concordance,Collection
        collectionMap = {'Simons Twins Collection': 'stc', 'Simons Simplex Collection': 'ssc'}
        for l in f:
            cs = l.strip().split(",")
            if len(cs) != 7:
                raise Exception('ccc')

            (familyId,prbCode,twnCodesS,twnRolesS,zygosity,concordance,collection) = cs
            codes = twnCodesS.split("/ ")
            roles = twnRolesS.split("/ ")

            codes.append(prbCode)
            roles.append("proband")
            if len(codes) != len(roles):
                raise Exception('codes and roles have different length')

            tg = TwinGroup()
            tg.zygosity = zygosity
            tg.collection = collectionMap[collection]
            tg.twins = set()

            for cd,rl in zip(codes,roles):
                personId = familyId+"."+cd
                if personId in self.individual:
                    p = self.individual[personId]
                else:
                    print >>sys.stderr, "the twin", personId, "is not quite in the collection"
                    p = Person()
                    p.familyId = familyId
                    p.personId = familyId + "." + cd
                    p.role = rl
                    p.collection = tg.collection 

                if p.familyId != familyId or p.role != rl or p.collection != tg.collection: 
                    raise Exception("The person info from the twind file doesn't match the one in the individual file")
                tg.twins.add(p)
            # births = { p.birth for p in tg.twins if p.hasattr('birth') }
            births = set((p.birth for p in tg.twins if hasattr(p,'birth')))
            if len(births)!=1:
                print >>sys.stderr, births
                print >>sys.stderr, 'birth month mismatch for twins from family', familyId
   
            for p in tg.twins:
                if not hasattr(p,'birth'):
                    p.birth = iter(births).next()
            self.twinGroups.add(tg)
                    
            
    def _loadCollectionCenter(self):
        f = open(os.path.join(self.sfariDir,'ssc_age_at_assessment.csv'))

        f.readline()  # header 
        famCenterS = defaultdict(set) 
        for l in f:
            cs = l.strip().split(',')
            fm,role = cs[0].split('.')
            age = cs[1]
            center = cs[2]
            #famCenterS[fm].add(center)
            if fm not in self.familyCenter:
                self.familyCenter[fm]=center
                self.familyAgeAtAssement[fm]=age
            
        ## assert
        #if len([x for x in famCenterS.values() if len(x)>1])>0:
        #    raise Exception('aaa')
        #famCenter = {f:s.pop() for f,s in famCenterS.items() }
        
        f.close()
        
        #return famCenter

    def _loadIndividual(self):
        f = open(os.path.join(self.sfariDir,'individual.csv'))
        h = f.readline()
        for l in f:
            cs = l.strip().split(",")
            if len(cs) != 11:
                raise Exception('_loadIndividual failed')

            p = Person()
            (p.familyId,
             p.personId,
             p.sex,
             p.father,
             p.mother,
             p.birth,
             p.guid,
             p.role,
             p.genetic_ab,
             p.genetic_ab_notes,
             p.collection) = cs 
            if p.personId in self.individual:
                raise Exception('person ' + p.personid + ' is defined twice')
            self.individual[p.personId] = p
        
    def _testCollection(self):
        allOk = True

        ## test that each 
        fmCl = defaultdict(set)
        for p in sc.individual.values():
            fmCl[p.familyId].add(p.collection)

        for fid,css in fmCl.items():
            if len(css)!=1:
                print >>sys.stderr, "The family ", fid, "is in more than one collection"
                allOK = False
            

        ## test that samples are from known individual            
        sui = 0
        for s in self.sample.values():
            if s.personId not in self.individual:
                sui+=1
                print >>sys.stderr, str(sui) + ". the person for sample", s.sampleId, "is not in the collection" 
                allOk = False
            
if __name__ == "__main__":
    sc = SfariCollection()

    # sc._testCollection()
    
