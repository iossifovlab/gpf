#!/data/software/local/bin/python
import os
import os.path
import glob
import csv

dataDir=os.environ['T94_PROJECT_DIR']+"/data"
outputDir=os.environ['T94_PROJECT_DIR']+"/chips"

for batchDir in glob.glob(dataDir+"/batch*"):
    batchNumber=os.path.basename(batchDir)[5:]
    locations=[]
    # a requests folder may not exist in an older batch so check if it exists
    if os.path.exists(batchDir+"/requests"):
        #get the locations from all of the request files
        for requestFile in glob.glob(batchDir+"/requests/*.txt"):
            with open(requestFile,'r') as inputFile:
                inputReader=csv.DictReader(inputFile,delimiter="\t")
                for row in inputReader:
                    locations.append(row["location"])
    else:
        #get the locations from all of the report files
        for reportFile in glob.glob(batchDir+"/reports/report*.txt"):
            with open(reportFile,'r') as inputFile:
                inputReader=csv.DictReader(inputFile,delimiter="\t")
                for row in inputReader:
                    locations.append(row["location"])

    bedRows=[]
    # only include a location once, if a location is the same as a previous
    # location skip it
    existingLocations={}
    for location in locations:
        if location in existingLocations:
            continue
        existingLocations[location]=True
        row=[]
        split=location.split(":")
        pos=int(split[1])

        # if position of the variant is less than 400bp from the beginning of
        # the chromosome, then the start position needs to be set to 0.
        startPos=pos-400
        if startPos < 0:
            startPos=0
        endPos=pos+400
        # In the reference files used by GATK the mitochondrial chromosome is
        # labeled MT, not M, so the chromosome needs to be renames in order
        # for quad processing to work properly.
        if split[0]=="M" or split[0]=="MT":
            split[0]="MT"
            # the end position must not be greater than the length of the chromosome.This occurs if the variant location is within 400bp of the end of the chromosome.
            if endPos>16569:
                endPos=16569
        elif split[0]!="X" and split[0]!="Y" and split[0]:
            split[0]=int(split[0])
            
        bedRows.append([split[0],startPos,endPos])

    # merge overlapping regions
    overlapFound=True
    while overlapFound:
        rowsToDelete=[]
        for i in range(0,len(bedRows)-1):
            for j in range(1,len(bedRows)):
                if i!=j and i not in rowsToDelete and j not in rowsToDelete and bedRows[i][0]==bedRows[j][0]:
                    overlap=max(0, min(bedRows[i][2],bedRows[j][2] ) - max(bedRows[i][1], bedRows[j][1]))
                    if overlap>0:
                        # expand the current row
                        bedRows[i][1]=min(bedRows[i][1],bedRows[j][1])
                        bedRows[i][2]=max(bedRows[i][2],bedRows[j][2])
                        #delete the overlapping row
                        rowsToDelete.append(j)
        if len(rowsToDelete)>0:
            overlapFound=True
            
            # delete the indexes in reverse order so as not to change the indexes
            # of the values you are deleting.
            uniqueIndexes=set(rowsToDelete)
            rowsToDelete=list(uniqueIndexes)
            rowsToDelete.sort(reverse=True)
            for index in rowsToDelete:
                del bedRows[index]
        else:
            overlapFound=False
               
    outFileName=outputDir+"/"+"v"+batchNumber+".400.target.bed"
    bedRows.sort()
     
    with open(outFileName,"w") as outFile:
        writer=csv.writer(outFile,delimiter="\t")
        writer.writerows(bedRows)

    outZipFileName=outputDir+"/"+"v"+batchNumber+".400.probe.bed.gz"

    os.system("gzip < " + outFileName + " > " + outZipFileName)
