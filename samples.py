#!/data/software/local/bin/python

from DAE import *

sfariDB.individual
print ",sample_id,person_id,sample_type,FamilyId,Gender,RelationToProband,Source,ENDC,,"
for x in sfariDB.sample.values():
    fid=x.sampleId.rsplit('.')[0]
    if (fid != 'id()'):
        sampleType = x.sampleType
        if (sampleType == "wb-dna"):
            sampleType = "whole blood"

        if x.personId in sfariDB.individual.keys() and sfariDB.individual[x.personId].collection == "ssc":
            p=sfariDB.individual[x.personId]
            familyId = p.familyId
            if (p.sex == "female"):
                Gender = "F"
            elif (p.sex == "male"):
                Gender = "M"
            else:
                print "Strange gender ", p.sex, "\n"
            role = p.role
            if (p.role == "proband"):
                role = "self"
            elif (p.role == "designated-sibling" or p.role == "other-sibling"):
                role = "sibling"
            elif (role == "mother"):
                role = "mother"
            elif (role == "father"):
                role = "father"
            else:
                print "Strange role ",  role, "\n"

            print "%s,%s,%s,%s,auSSC%s,%s,%s,%s"  %("RR",x.sampleNumber,x.sampleNumber,sampleType,familyId,Gender,role,"Rutgers University DNA & Cell Repository; SSC Collection,,,")
    

    

    
    

