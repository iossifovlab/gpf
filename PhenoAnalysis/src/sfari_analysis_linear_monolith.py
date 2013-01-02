'''
Created on Dec 3, 2012

@author: Tony

Design of the command line tool

    Plan
        * fix the dt sturcture. dt['1111.p1']['IQ']
        * implement laodFromRawTable // paresed the v14.1.all..... and reture dt
        * fix the md structure
        * impelemtn imputeMetaData(dt) -> md
        * implement runHyperGeometirTest(dt,md,'outputfile')
        * how long does the load..Raw.. take and how long does the imputeMetadat take..?
        * assuming that laod is slow (more that 2mins)
            - implement saveInH5(dt) -> H5 file
            - implement loadFromH5(h5file) -> dt
            - how long does loadFromH5 take?
            - (optional) implement saveInTupples(dt) -> tupples
            - (optional) implement laodFromTupples(tupples file ) -> dt
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
def loadData(filename, createWords, rowsToLoad=-1, includeEmptyValues=True):
    columns = []
    columnsMember = {}    
    startOfVariables = 17
    
    inputfile = open(filename,"rUb")
    csvReader = csv.reader(inputfile, delimiter=',')
        
    lenPortalId=0
    lenVariableName=0
    lenVariableValue=0
        
    variables = {}
    
    dt = []    
            
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
                        columnsMember[column]['member'] = 'p2'                    
                    columnsMember[column]['variable'] = column[1:]                     
                i += 1
                
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
                    
                    if len(personId)>lenPortalId:
                        lenPortalId=len(personId)                    
                    if len(variableName)>lenVariableName:
                        lenVariableName=len(variableName)                    
                        
                    if createWords == True:                                
                        #parse variableValue into seperate words
                        words = findWords(variableValue)           
                        for word in words:                           
                            dt.append([personId, variableName, word])    
                            if len(word)>lenVariableValue:
                                lenVariableValue=len(word)                                                    
                    else:                       
                        dt.append([personId, variableName, variableValue])                                                                                               
                        if len(variableValue)>lenVariableValue:
                            lenVariableValue=len(word)                                                    
                        
        idx+=1
        
    inputfile.close()                              

    return dt,lenPortalId,lenVariableName,lenVariableValue

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
#    md[variableName]
#    md[variableName][datatype]

def imputeMetaData(dt):
    
    datatypeProportionThreshold = 0.95
    
    variables={}
    md = {}
    for row in dt:
        variableName = row[1]
        variableValue = row[2]
        
        if variableName not in variables:
            dataType = getDataType(variableValue)         
            variables[variableName] = {'datatype':{'empty':0,'numeric':0,'float':0,'integer':0,'boolean':0,'date':0,'string':0},'values':{}}
            variables[variableName]['datatype'][dataType]=1         
            md[variableName] = {'datatype':'unknown','values':[],'uniqueValues':0}
        else:
            dataType = getDataType(variableValue)            
            variables[variableName]['datatype'][dataType]+=1     
    
        if variableValue not in variables[variableName]['values']:
            variables[variableName]['values'][variableValue] = 1
        else:
            variables[variableName]['values'][variableValue] += 1

        
    print "There are %d variable keys"%(len(variables))
    
    for variableName in variables.keys():
   
        dataTypes = variables[variableName]['datatype']
    
        #dataTypeDict =  variables[variableName]['datatype']    
        valueDict = variables[variableName]['values']
        numValues = len(valueDict)
                             
        #numValuesariables = variables[variableName]['values'].keys()
        #values = 
    
        #sortedValues = sorted(valueDict, key=valueDict.get, reverse=True)
        #values = valueDict.values()    
        #tokenCount = sum(np.array(values))        
    
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
                #md[variableName]['values'] = sorted(variables[variableName]['values'].keys())
     
        md[variableName]['values'] = sorted(variables[variableName]['values'].keys())     
        md[variableName]['datatype'] = dataType
        md[variableName]['uniqueValues'] = numValues

    return md

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
        #values = ''
        #if (datatype=='label'):            
        values = '|'.join(variable['values'])         
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
                    values = person['variables'][variableName]
                    for value in values:
                        if value not in wordBag:
                            wordBag[value]={'entireRef':0, 'wiglerRef':0, 'eichlerRef':0, 'stateRef':0, 'entireFam':{}, 'wiglerFam':{}, 'eichlerFam':{}, 'stateFam':{}}                        
                        
                        if family not in wordBag[value]['entireFam']:
                            wordBag[value]['entireFam'][family]=True                        
                            
                        wordBag[value]['entireRef']+=1                        
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
                        values = person['variables'][variableName]
                        for value in values:
                                                        
                            #if familySetName not in wordBag[value]:
                            #    wordBag[value][familySetName+"Ref"]=0
                            #    wordBag[value][familySetName+"Fam"]=0
                             
                            if family not in wordBag[value][familySetName+"Fam"]:
                                wordBag[value][familySetName+"Fam"][family]=True
                                                                                                          
                            wordBag[value][familySetName+"Ref"]+=1                        
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
    
    print "totalCountInSetA=%d"%(totalCountInSetA)
    print "totalCountInSetB=%d"%(totalCountInSetB)
                          
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
        countInB = len(word['entireFam'])
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

if os.path.exists(h5Filename):
    
    # Too slow.
    start_time = time()
    dt = loadDataFromH5(h5Filename)    
    print "loadDataFromH5 ", time() - start_time, "seconds"
    
    #h5 = openDataFromH5(h5Filename)
        
    start_time = time()
    md = loadMetaData(mdFilename)    
    print "loadMetaData ", time() - start_time, "seconds"
    print "md is %d bytes"%(sys.getsizeof(md))
        
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
    print "createWordBag ", time() - start_time, "seconds"        

    start_time = time()
    wordBag = createWordBagFamilySet(wordBag, dt, md, eichlerFamily, "eichler")
    print "createWordBag ", time() - start_time, "seconds"        

    start_time = time()
    wordBag = createWordBagFamilySet(wordBag, dt, md, stateFamily, "state")
    print "createWordBag ", time() - start_time, "seconds"        

    start_time = time()
    saveWordBag(wordBag, wordBagFilename)
    print "saveWordBag ", time() - start_time, "seconds"        

    
    start_time = time()    
    runHyperGeometricTest(dt, md, wordBag, allFamily, wiglerFamily)
    print "runHyperGeometricTest ", time() - start_time, "seconds"
            
    
    
else:     
    start_time = time()
    dt,lenPortalId,lenVariableName,lenVariableValue = loadData(filename, createWords, rowsToLoad)
    print "loadData ", time() - start_time, "seconds"  
    print "df contain %d rows"%(len(dt))
    print "df lenPortalId %d"%(lenPortalId)
    print "df lenVariableName %d"%(lenVariableName)
    print "df lenVariableValue %d"%(lenVariableValue)
    
    start_time = time()
    saveDataToH5(dt, h5Filename, lenPortalId, lenVariableName, lenVariableValue)
    print "saveDataToH5 ", time() - start_time, "seconds"  
    print "df contain %d rows"%(len(dt))

    start_time = time()
    md = imputeMetaData(dt)
    print "imputeMetaData ", time() - start_time, "seconds"  

    start_time = time()
    saveMetaData(md, mdFilename)
    print "saveMetaData ", time() - start_time, "seconds"  
    

    