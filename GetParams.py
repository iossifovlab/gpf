#!/data/software/local/bin/python

"""
This script finds all the params file in a given directory and gets
the path where the params file is located and gets the contents of the params
file and puts the data into a tab delimited text file
"""


import os
import csv

# TODO: Get path from environment
toplevelDir=os.environ['T94_PROJECT_DIR']+"/objLinks"
outputFile="objectGraph.txt"

data=[]

for dirpath,dirnames,filenames in os.walk(toplevelDir,followlinks=True):
    if "params.txt" in filenames:
        row=[dirpath]
        with open(dirpath+"/params.txt",'r') as paramFile:
            contents=paramFile.read()
            row.append(contents)
        data.append(row)
            
with open(outputFile,'w') as outFile:
    writer=csv.writer(outFile,delimiter="\t")
    writer.writerow(["path","params"])
    writer.writerows(data)
                    
