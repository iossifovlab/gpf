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