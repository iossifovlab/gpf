#!/usr/bin/env python
'''
Created on Dec 3, 2012

@author: Tony

Design of the command line tool

    Plan
        * fix the dt sturcture. dt['1111.p1']['IQ']
        * implement loadFromRawTable // paresed the v14.1.all..... and reture dt
        * fix the md structure
        * impelemtn imputeMetaData(dt) -> md
        * implement runHyperGeometirTest(dt,md,'outputfile')
        * how long does the load..Raw.. take and how long does the imputeMetadat take..?
        * assuming that load is slow (more that 2mins)
            - implement saveInH5(dt) -> H5 file
            - implement loadFromH5(h5file) -> dt
            - how long does loadFromH5 take?
            - (optional) implement saveInTupples(dt) -> tupples
            - (optional) implement loadFromTupples(tupples file ) -> dt
            - (optional) how long does loadFromTupples take?
        * assuming that the imputeMetaData is slow (>1mins)
            - implement saveMetaData(md) -> metaDataFile
            - implement loadMetaData(metaDataFile) -> md
            
    Command line parameters
    xxxx.py dataFile fileWithFamilyId outputFile [metaDataFile] 
    
    1. dt = loadData()        
        1a. dt = loadDataFromRawTable()
        1b. dt = loadDataFromH5();
        1c. dt = loadDataFromTupples()
        1d. ...
    2a. md = imputeMetaData(dt);
    2b. md = loadMetaData(dt);
    3. runHyperGeometricTest(dt, md, FamilySet) // like DELIVERABLE 2 with udpdates
        The output columns:
            1. Token
            2. Total number of families (boring)
            3. Familes that have the token
            4. Families in the Family set (boring)
            5. "moreOrLess"
            6. p-value
            7. Expected overlap (ht.mean())
            8. The observed overlat (the number of "family set" that have the token)
        Pseudo-code:
            - wordBags = createWordBags(dt, md)
            - for w in ..
            .....
            
    4. runTestForTheNumericalFields(dt, FamilySet) // like DELIVARABLE 3
    
'''
import csv
from time import clock, time
from utils import *
import tables
from tables import StringCol, Col
import os
import numpy as np
import sys



# given 
#     filename : the SFARI data dump
#     createWords : if true, values will be broken into words. 
# returns dt,lenPortalId,lenVariableName,lenVariableValue
def loadFromRawTable(filename, rowsToLoad=-1):
    columns = []
    columnsMember = {}    
    startOfVariables = 17
    includeEmptyValues=False
    
    createVars = False
    
    inputfile = open(filename,"rUb")
    csvReader = csv.reader(inputfile, delimiter=',')
    
    if createVars:
        varsFile = open("data/loadFromRawTable.csv", "wb")
    
    variables = {}
    
    dt = {}
            
    idx = 0
    for row in csvReader:    
      
        if (idx%100)==0:
            print idx
    
        if rowsToLoad>-1:
            if rowsToLoad==idx:
                break
                    
        if idx == 0:      
            i = 0      
            for column in row:
                columns.append(column)
                columnsMember[column] = {}
                
                if i < startOfVariables:  
                    columnsMember[column]['member'] = 'p1'
                    columnsMember[column]['variable'] =  column                   
                else: 
                    first = column[0:1]               
                    if (first == 'p'):             
                        columnsMember[column]['member'] = 'p1'                                                                
                    elif (first == 's'):
                        columnsMember[column]['member'] = 's1'
                    elif (first == 'm'):
                        columnsMember[column]['member'] = 'mo'
                    elif (first == 'f'):
                        columnsMember[column]['member'] = 'fa'
                    elif (first == 't'):
                        columnsMember[column]['member'] = 'p1'                    
                    columnsMember[column]['variable'] = column[1:]                     
                i += 1
                
                if createVars:
                    buf = "%d %s %s\n"%(i,column,columnsMember[column]['member'])                
                    varsFile.write(buf)
                
            numCols = len(columns)
        
        else:    
            family = row[0]
            
            for i in range(0,numCols):
                variableValue = row[i].strip()
                     
                if len(variableValue)==0:
                    isEmpty = True
                else:
                    isEmpty = False
                    
                if (isEmpty == False) or (isEmpty == True and includeEmptyValues == True):                                                                
                    columnName = columns[i]
                    memberCode = columnsMember[columnName]['member']                    
                    personId = family +  "."  + memberCode
                    variableName = columnsMember[columnName]['variable']   
                    
                    if personId not in dt:
                        dt[personId] = {} 
                                                                                                                    
                        dt[personId]['family']=family
                        dt[personId]['member']=memberCode
                        dt[personId]['variables']={}
                                                                                                                                                                  
                    dt[personId]['variables'][variableName]=variableValue
                                                
        idx+=1
        
    inputfile.close()                              
    if createVars:
        varsFile.close()

    return dt

# given 
#    dt
#    filename
# create a H5
def saveDataToH5(dt, filename, lenPortalId, lenVariableName, lenVariableValue):    
            
    h5File = tables.openFile(filename, mode = "w", title = "Data Tuples")
    group = h5File.createGroup("/", 'tuples', 'Tuples')
    filters = tables.Filters(complevel=9, complib='blosc')
    table = h5File.createTable(group, 'data', {'id':StringCol(lenPortalId),'key':StringCol(lenVariableName),'value':StringCol(lenVariableValue)}, "Data", filters=filters)
    particle = table.row
                                          
    for row in dt:           
        particle['id'] = row[0]    
        particle['key'] = row[1]
        particle['value'] = row[2]                                
        particle.append()
    
    table.flush()
    h5File.flush()               
    h5File.close()

# given
#    h5Filename
# return dt 
# 12/4/2012 This function has a severe bug and crashes
def loadDataFromH5(h5Filename):
        
    dt = {}
    h5File=tables.openFile(h5Filename,'r')
    
    table = h5File.root.tuples.data
        
    idx=0
    for row in table.iterrows():
        
        #if (idx%100000)==0:
        #    print idx        
        personId = row['id']
        key = row['key']
        value = row['value']

        if personId not in dt:
            dt[personId]={}            
                    
            data = personId.split(".")
            dt[personId]['family']=data[0] 
            dt[personId]['member']=data[1]
            dt[personId]['variables']={}
            dt[personId]['variablesRaw']={}
            
        if key not in dt[personId]['variables']:  
            dt[personId]['variables'][key]=[]
            
            
        dt[personId]['variables'][key].append(value)
        dt[personId]['variablesRaw'][key]=value
                      
        idx+=1
         
    h5File.close()    
    
    return dt
   
   
# given
#    h5Filename
# return dt 
# 12/4/2012 This function has a severe bug and crashes
def openDataFromH5(h5Filename):        
    h5File=tables.openFile(h5Filename,'r')    
    return h5File
   
# load CSV
# return a md              
def loadMetaData(mdFilename):
    md = {}    
    
    inputfile = open(mdFilename,"rUb")
    csvReader = csv.reader(inputfile, delimiter=',')
                
    for row in csvReader:    
        md[row[1]]={}
        md[row[1]]['datatype']=row[2]
        md[row[1]]['uniqueValues']=row[3]                                                     
        md[row[1]]['values']=row[4].split('|')        
                
    inputfile.close()                              

    return md
                 
# given dt
# returns md
# meta data :
# 
#    md[variableName]['datatype'] = str  label, text, numeric, unknown
#    md[variableName]['values'][value] = count 
#    md[variableName]['member'][member] = count;

# bug?
# md[variableName]['values'] = sorted(variables[variableName]['values'].keys())

def imputeMetaData(dt):
    
    datatypeProportionThreshold = 0.95
    
    variables={}
    md = {}
    members={}
    for personId in dt.keys():
        person = dt[personId]
                
        for variableName in person['variables']:
            variableValue = person['variables'][variableName]
        
            if variableName not in variables:
                dataType = getDataType(variableValue)         
                variables[variableName] = {'datatype':{'empty':0,'numeric':0,'float':0,'integer':0,'boolean':0,'date':0,'string':0},'values':{}}
                variables[variableName]['datatype'][dataType]=1         
                md[variableName] = {'datatype':'unknown','values':{},'uniqueValues':0,'members':{}}
            else:
                dataType = getDataType(variableValue)            
                variables[variableName]['datatype'][dataType]+=1     
        
            if variableValue not in variables[variableName]['values']:
                variables[variableName]['values'][variableValue] = 1                            
            else:
                variables[variableName]['values'][variableValue] += 1

            member = dt[personId]['member']
            
            if member not in members:
                members[member]=True
                
            if member not in md[variableName]['members']:
                md[variableName]['members'][member] = 1
            else:
                md[variableName]['members'][member] += 1
        
    print "There are %d variable keys"%(len(variables))
    
    for variableName in variables.keys():
   
        dataTypes = variables[variableName]['datatype']        
        valueDict = variables[variableName]['values']
        numValues = len(valueDict)
                             
        dataType = 'unknown'                           
                             
        if dataTypes['empty'] == numValues:
            dataType = 'empty'
                             
        if dataTypes['numeric'] > 0 and dataTypes['string'] > 0:
            if float(dataTypes['numeric'])/float(dataTypes['string']) >  datatypeProportionThreshold:
                dataType = 'numeric'
            elif float(dataTypes['string'])/float(dataTypes['numeric']) >  datatypeProportionThreshold:
                dataType = 'string'
            else:
                dataType = 'string'
        elif dataTypes['numeric'] > 0:
            dataType = 'numeric'
        elif dataTypes['string'] > 0:
            dataType = 'string'
                    
        if (dataType == 'string'):
            if numValues>20:
                dataType = 'text'
                
            else:  
                dataType = 'label'
                 
        md[variableName]['datatype'] = dataType
        md[variableName]['uniqueValues'] = numValues
        md[variableName]['values'] = variables[variableName]['values']

    return md,members

def createMetaDataReport(md, members, filename):
    maxVars = 20
    
    f = open(filename, 'wb')       
    writer = csv.writer(f) 
    
    
    #Variable    
    #Data Type   
    #Number of Distinct values
    #Total tokens    
    #Tokens with the top values    
    #Mother    
    #Father    
    #Proband    
    #Sibling    
    #Most Used 0   
    #Most Used 1    
    #Most Used 2    
    #Most Used 3    
    #Most Used 4    
    #Most Used 5    
    #...

            
    row = []    
    row.append("Variable")
    row.append("Data Type")
    row.append("Number of Distinct values")
    row.append("Total tokens")
    row.append("Tokens with the top values")
    
    for x in sorted(members.keys()):
        row.append(x)
            
    for x in range(maxVars):
        row.append("Most Used " + str(x))    
    
    writer.writerow(row)
    
    keys = sorted(md.keys())
    
    index=1
    for variableName in keys:
        variable = md[variableName]
        datatype = variable['datatype']  
        values = '|'.join(variable['values'])         
        uniqueValues = variable['uniqueValues']  
        
        valueDict = md[variableName]['values']
        numUnique = len(valueDict)
        #rs = rolesS[variableName]   
        sortedValues = sorted(valueDict, key=valueDict.get, reverse=True)
        values = valueDict.values()    
        tokenCount = sum(np.array(values))        
        tokenInMostUsed = sum(np.array([valueDict[x] for x in sortedValues[0:maxVars]]))
        mostUsed = "\t".join([ x + ";" + str(valueDict[x])   for x in sortedValues[0:maxVars]])
                
        row = []
        #row.append(index)
        row.append(variableName)
        row.append(datatype)
        #row.append(values)        
        row.append(str(numUnique))
        row.append(str(tokenCount))
        row.append(str(tokenInMostUsed))
    
    
        for member in members.keys():
            if member in md[variableName]['members']:
                row.append(md[variableName]['members'][member])
            else:
                row.append("0")
                    
        for x in sortedValues[0:maxVars]:
            row.append(x + ";" + str(valueDict[x]))   
                            
        writer.writerow(row)
        index+=1        
    f.close()

def saveMetaData(md, filename):
    
    f = open(filename, 'wb')       
    writer = csv.writer(f) #,lineterminator="\n") # delimiter=',',quoting=csv.QUOTE_MINIMAL)
            
    row = []
    row.append("index")
    row.append("variableName")
    row.append("datatype")
    row.append("uniqueValues")
    row.append("values")   
    writer.writerow(row)
    
    keys = sorted(md.keys())
    
    index=1
    for variableName in keys:
        variable = md[variableName]
        datatype = variable['datatype']                  
        
        values = '|'.join(sorted(variable['values'].keys()))         
        uniqueValues = variable['uniqueValues']  
        
        row = []
        row.append(index)
        row.append(variableName)
        row.append(datatype)
        row.append(uniqueValues)
        row.append(values)        
            
        writer.writerow(row)
        index+=1        
    f.close()


def createWordBag(dt, md):
    wordBag = {}    
    
    for personId in dt.keys():
        person = dt[personId]
        
        family = person['family']            
        member = person['member']
        
        process=False
        if member!='p1':
            continue
        
        for variableName in person['variables']:
            if variableName in md:
                datatype = md[variableName]['datatype']
                if datatype == 'string' or datatype == 'label':
                    variableValue = person['variables'][variableName]
                   
                    words = findWords(variableValue)                                                            

                    for word in words:
                        if word not in wordBag:
                            wordBag[word]={'entireRef':0, 'wiglerRef':0, 'eichlerRef':0, 'stateRef':0, 'entireFam':{}, 'wiglerFam':{}, 'eichlerFam':{}, 'stateFam':{}}                        
                        
                        if family not in wordBag[word]['entireFam']:
                            wordBag[word]['entireFam'][family]=True                        
                            
                        wordBag[word]['entireRef']+=1                        
                else:
                    continue                
    return wordBag


def createWordBagFamilySet(wordBag, dt, md, familySet, familySetName):    
    
    for personId in dt.keys():
        person = dt[personId]
        
        family = person['family']            
        member = person['member']
        
        process=False
        if member!='p1':
            continue
        
        if family in familySet:
            for variableName in person['variables']:
                if variableName in md:
                    datatype = md[variableName]['datatype']
                    if datatype == 'string' or datatype == 'label':
                        variableValue = person['variables'][variableName]
                                                
                        words = findWords(variableValue)                                                            

                        for word in words:
                             
                            if family not in wordBag[word][familySetName+"Fam"]:
                                wordBag[word][familySetName+"Fam"][family]=True
                                                                                                          
                            wordBag[word][familySetName+"Ref"]+=1                        
                    else:
                        continue                
    return wordBag


# given dt, md, FamilySet
# creates output csv
#
# The output columns:
# 1. Token
# 2. Total number of families (boring)
# 3. Familes that have the token
# 4. Families in the Family set (boring)
# 5. "moreOrLess"
# 6. p-value
# 7. Expected overlap (ht.mean())
# 8. The observed overlat (the number of "family set" that have the token)
  
import scipy.stats as stats
  
def runHyperGeometricTest(dt, md, wordBag, setA, setB):

    totalCountInSetA = len(setA)
    totalCountInSetB = len(setB)
                              
    f = open("data/HyperGeometricTest.csv", 'wb')       
    writer = csv.writer(f)
        
    row = []
    row.append("Token")
    row.append("Total number of families")
    row.append("Families that have the token")
    row.append("Families in the Family set")
    row.append("More or Less")
    row.append("p-value")
    row.append("Expected overlap")
    row.append("Observed overlap")
    
    writer.writerow(row)
    
    keys = sorted(wordBag.keys())    
    for key in keys:
        word = wordBag[key]
        row = []
        row.append(key)
       
        countInA = len(word['entireFam'])
        countInB = len(word['wiglerFam'])
        hg = stats.hypergeom(totalCountInSetA,countInA,countInB)
        x = 0.0
        xb = x
        hgMean = hg.mean()
        xs =hgMean - (x - hgMean)
        if x < hg.mean():
            xs = x
            xb = hgMean + (hgMean - x)
            moreOrLess = "less"
        else:
            moreOrLess = "More"
        
        #print xs,xb
        #print hg.cdf(xs), hg.cdf(xb), 1.0 - float(hg.cdf(xb))
        #if hg.cdf(xb)>1.0:
        #    print "WWWWWWW"
        
        pValue = hg.cdf(xs) + 1.0 - hg.cdf(xb)
                            
        row.append(totalCountInSetA)
        row.append(countInA)
        row.append(totalCountInSetB)
        row.append(moreOrLess)
        row.append(pValue)
        row.append(hgMean)
        row.append(countInB)
                                  
        writer.writerow(row)
        
    f.close()
    
               
                
# given dt, md, FamilySet
# creates output csv
def runTestForTheNumericalFields(dt, FamilySet):
    pass


# if it does not already exist ...
# creates a family list for Eichler from nature paper attachment

def generateEichlerFamilyFile():

    filename = "data/eichlerFamily.csv"
    
    if os.path.exists(filename):
        return
        
    families = {}

    inputfile = open("data/nature10989-s2.csv","rUb")
    csvReader = csv.reader(inputfile, delimiter=',')    
    for row in csvReader:    
        child = row[0]
        if len(child)==8:
            familyId = child[0:5]    
            if len(familyId)==5:
                families[familyId] = []
    
    inputfile.close()
    
    f = open(filename, 'wb')       
    writer = csv.writer(f)
        
    row = []
    row.append("family")
    writer.writerow(row)
    
    keys = sorted(families.keys())    
    for family in keys:
        row = []
        row.append(family)
        writer.writerow(row)
        
    f.close()
          
# if it does not already exist ...
# creates a family list for State from nature paper attachment
    
def generateStateFamilyFile():

    filename = "data/stateFamily.csv"
    
    if os.path.exists(filename):
        return
    
    
    families = {}

    inputfile = open("data/nature10945-s2.csv","rUb")
    
    csvReader = csv.reader(inputfile, delimiter=',')    
    for row in csvReader:    
        familyId = row[0]   
        if len(familyId) == 5:
            if familyId not in families:
                families[familyId] = []
    
    inputfile.close()
    
    f = open(filename, 'wb')       
    writer = csv.writer(f)
        
    row = []
    row.append("family")
    writer.writerow(row)
    
    keys = sorted(families.keys())    
    for family in keys:
        row = []
        row.append(family)
        writer.writerow(row)
        
    f.close()
    
def saveWordBag(wordBag, wordBagFilename):
    f = open(wordBagFilename, 'wb')       
    writer = csv.writer(f)
        
    row = []
    row.append("word")
    row.append("entireRef")
    row.append("wiglerRef")
    row.append("eichlerRef")
    row.append("stateRef")
    row.append("entireFam")
    row.append("wiglerFam")
    row.append("eichlerFam")
    row.append("stateFam")
    writer.writerow(row)
    
    keys = sorted(wordBag.keys())    
    for key in keys:
        word = wordBag[key]
        row = []
        row.append(key)
        row.append(word['entireRef'])
        row.append(word['wiglerRef'])
        row.append(word['eichlerRef'])
        row.append(word['stateRef'])                                
        row.append(len(word['entireFam']))
        row.append(len(word['wiglerFam']))
        row.append(len(word['eichlerFam']))
        row.append(len(word['stateFam']))                                
        writer.writerow(row)        
    f.close()
                                    
# given
#     filename
# return
#    dictionary of family ids
def loadFamilyList(filename):
    familyList = {}    
    
    inputfile = open(filename,"rUb")
    csvReader = csv.reader(inputfile, delimiter=',')
                
    idx=0
    for row in csvReader:
        if idx>0:    
            familyList[row[0]]=True
        idx+=1
            
    inputfile.close()                              

    return familyList

def debug():        
    #------------------------------------------------------------------------------
    mdFilename = "data/metadata.csv"
    filename = "data/14_EVERYTHING.csv"
    h5Filename = "data/tuples.h5"
    wordBagFilename = "data/wordbag.csv"
    allFamilyFilename = "data/all_family.csv"
    wiglerFamilyFilename = "data/wigler_343_family.csv"
    eichlerFamilyFilename = "data/eichlerfamily.csv"
    stateFamilyFilename = "data/statefamily.csv"
    
    createWords = True
    rowsToLoad = -1  #all is -1
    
    generateEichlerFamilyFile()
    generateStateFamilyFile()
     
    start_time = time()
    dt = loadFromRawTable(filename, rowsToLoad)
    print "loadData ", time() - start_time, "seconds"  
    print "df contain %d rows"%(len(dt))
    
    start_time = time()
    md, members = imputeMetaData(dt)
    print "imputeMetaData ", time() - start_time, "seconds"  
    
    start_time = time()
    saveMetaData(md, mdFilename)
    print "saveMetaData ", time() - start_time, "seconds"  
    
    start_time = time()
    createMetaDataReport(md, members, "data/ivansFirstVariables20.csv")
    print "createMetaDataReport ", time() - start_time, "seconds"  
    
    start_time = time()
    allFamily = loadFamilyList(allFamilyFilename)    
    print "loadFamilyList ", time() - start_time, "seconds"
      
    start_time = time()
    wiglerFamily = loadFamilyList(wiglerFamilyFilename)    
    print "loadFamilyList ", time() - start_time, "seconds"
    
    start_time = time()
    eichlerFamily = loadFamilyList(eichlerFamilyFilename)    
    print "loadFamilyList ", time() - start_time, "seconds"
    
    start_time = time()
    stateFamily = loadFamilyList(stateFamilyFilename)    
    print "loadFamilyList ", time() - start_time, "seconds"
            
    start_time = time()
    wordBag = createWordBag(dt, md)
    print "createWordBag ", time() - start_time, "seconds"        
    
    start_time = time()
    wordBag = createWordBagFamilySet(wordBag, dt, md, wiglerFamily, "wigler")
    print "createWordBagFamilySet ", time() - start_time, "seconds"        
    
    start_time = time()
    wordBag = createWordBagFamilySet(wordBag, dt, md, eichlerFamily, "eichler")
    print "createWordBagFamilySet ", time() - start_time, "seconds"        
    
    start_time = time()
    wordBag = createWordBagFamilySet(wordBag, dt, md, stateFamily, "state")
    print "createWordBagFamilySet ", time() - start_time, "seconds"        
    
    start_time = time()
    saveWordBag(wordBag, wordBagFilename)
    print "saveWordBag ", time() - start_time, "seconds"        
    
    start_time = time()    
    runHyperGeometricTest(dt, md, wordBag, allFamily, wiglerFamily)
    print "runHyperGeometricTest ", time() - start_time, "seconds"
    
    
