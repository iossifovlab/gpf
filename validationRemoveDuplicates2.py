#!/bin/env python
from __future__ import print_function
from builtins import map
from DAE import *

filteredValidationRows={}

for v in vDB.get_validation_variants():
    row={
        "familyId":v.familyId,
        "location":v.location,
        "variant":v.variant,
        "val.batchId":v.batchId,
        "val.valStatus":v.valStatus,
        "val.resultNote":v.resultNote,
        "val.counts":mat2Str(v.valCounts),
        "val.parent":v.valParent
        }
    key="_".join(map(str,(v.familyId,v.location,v.variant)))
    if key not in filteredValidationRows:
        filteredValidationRows[key]=row
    else:
        oldRow=filteredValidationRows[key]
	oldRowStatus=oldRow["val.valStatus"].strip()
        oldBatchNumber=int(oldRow["val.batchId"][5:])
        rowBatchNumber=int(row["val.batchId"][5:])
	rowStatus=row["val.valStatus"].strip()
        if oldRowStatus=="valid" and rowStatus=="valid" and rowBatchNumber>oldBatchNumber:
            filteredValidationRows[key]=row
        elif oldRowStatus=="valid" and rowStatus=="failed":
            continue
        elif oldRowStatus=="failed" and rowStatus=="valid":
            filteredValidationRows[key]=row
        elif oldRowStatus=="invalid" and rowStatus=="invalid" and rowBatchNumber>oldBatchNumber:
            filteredValidationRows[key]=row
        elif oldRowStatus=="invalid" and rowStatus=="failed":
            continue
        elif oldRowStatus=="failed" and rowStatus=="invalid":
            filteredValidationRows[key]=row
        elif oldRowStatus=="failed" and rowStatus=="failed" and rowBatchNumber>oldBatchNumber:
            filteredValidationRows[key]=row
        elif oldRowStatus not in ["valid", "failed", "invalid"] and rowStatus in ["valid","failed","invalid"]:
            filteredValidationRows[key]=row
        elif oldRowStatus == "valid" and rowStatus=="invalid":
            errMsg="error: status contradiction for variant "+key
            raise Exception(errMsg)
        elif oldRowStatus == "invalid" and rowStatus=="valid":
            errMsg="error: status contradiction for variant "+key
            raise Exception(errMsg)

print("\t".join("familyId,location,variant,val.batchId,val.status,val.resultNote,val.counts,val.parent".split(",")))

for key,row in list(filteredValidationRows.items()):
    print("\t".join(map(str,(row["familyId"],row["location"],row["variant"],row["val.batchId"],
                             row["val.valStatus"],row["val.resultNote"],row["val.counts"],row["val.parent"]))))
    
