#!/bin/env python

'''
Created on Jun 25, 2013

@author: leotta
'''
import sys, getopt
import os
import re
import filecmp

def getComparison(commandsA, folderA, folderB):
    comparison = {}
    
    for i in commandsA.keys():
        name = "%s-out.txt"%(i)
        filenameA = os.path.join(folderA, name)
        filenameB= os.path.join(folderB, name)
        try:
            results = filecmp.cmp(filenameA, filenameB)
        except:
            results = False
        
        comparison[i]=results
        
    return comparison
    

def getFirstLine(filename):
    if os.path.exists(filename):
        f = open(filename, "r")
        first_line = f.readline()
        f.close
        return first_line
    else:
        return None
    
    
def getExitCodes(folder):

    exitCodes={}
    
    for f in os.listdir(folder):
        match = re.search(r'(^[0-9].*)-exitCode\.txt$', f)
        
        if match:
            index = int(match.group(1))
            
            filename = os.path.join(folder,f)
            
            exitCode = getFirstLine(filename)
            
            if exitCode==None:
                exitCode = 0
            else:
                exitCode = exitCode.strip()
            
            exitCodes[index]=exitCode

    return exitCodes


def getCommands(folder):

    commands={}
    
    for f in os.listdir(folder):
        match = re.search(r'(^[0-9].*)-cmd\.txt$', f)
        
        if match:
            index = int(match.group(1))
            
            filename = os.path.join(folder,f)
            
            command = getFirstLine(filename)
            
            if command==None:
                command = ""
            else:
                command = command.strip()
            
            commands[index]=command

    return commands

def compare(folderA,folderB):
    exitCodesA = getExitCodes(folderA)
    
    #print exitCodesA
    commandsA = getCommands(folderA)
    
    numberOfCmdsA = len(exitCodesA)

    exitCodesB = getExitCodes(folderB)
    
    #print exitCodesB
    
    commandsB = getCommands(folderB)
    numberOfCmdsB = len(exitCodesB)
    
    if numberOfCmdsA==numberOfCmdsB:
        comparisonAB = getComparison(commandsA, folderA, folderB)
    else:
        comparisonAB = {}
    
    
    #print numberOfCmdsB,exitCodesA
    #print numberOfCmdsB,exitCodesB
    #print numberOfCmdsB,comparisonAB

    cmds = sorted(commandsA.keys())

    for i in range(1,numberOfCmdsA+1):
        row=[]
        row.append(str(i))

        #print "A=%s B=%s"%(exitCodesA[i],exitCodesB[i])
         
        if exitCodesA[i]!='0' and exitCodesB[i]!='0':
            row.append('1_2_FAIL')

        elif exitCodesA[i]!='0' and exitCodesB[i]=='0':
            row.append('1_FAIL')

        elif exitCodesA[i]=='0' and exitCodesB[i]!='0':
            row.append('2_FAIL')
        
        elif comparisonAB[i]==True and exitCodesA[i]=='0' and exitCodesB[i]=='0':
            row.append('OK')
            
        elif comparisonAB[i]==False and exitCodesA[i]=='0' and exitCodesB[i]=='0':
            row.append('Diff')            
        
        else:
            row.append('Err')
            print [comparisonAB[i],exitCodesA[i],exitCodesB[i]]
            #row.append(":".join([comparisonAB[i],exitCodesA[i],exitCodesB[i]]))
            
            
            
        row.append(commandsA[i])
        
        print "\t".join(row)
        
    #Output
    # 
    #Column 1. Command Number
    #Column 2. Status
    #                OK if both runs finished on that command and the outputs are identical
    #                Diff if both runs finished on that command and the outputs are different
    #                1FAIL if the first run failed and the seconds succeeded
    #                2FAIL if the second run failed and the first succeeded
    #                1_2_FAIL if both runs failed
    #Column 3. The command

    
def usage(exitCode=0):
    print 'compareUT.py <folderA> <folderB>'
    sys.exit(exitCode)
    
def main(argv):
    folderA = None
    folderB = None
    #try:
    #    opts, args = getopt.getopt(argv, "a:b:", ["folderA=", "folderB="])
    #except getopt.GetoptError:
    #    usage(2)
    
    
    #for opt, arg in opts:
    #    if opt == '-h':
    #        usage()
    #    elif opt in ("-a", "--afolderA"):
    #        folderA = arg
    #    elif opt in ("-b", "--bfolderB"):
    #        folderB = arg

    if len(argv)>0:
    	folderA = argv[0]

    
    if len(argv)>1:
    	folderB = argv[1]

    if folderA == None:
        usage(2)

    if folderB == None:
        usage(2)
        
    #print 'UnitTest folder A is "', folderA
    #print 'UnitTest folder B is "', folderB

    compare(folderA,folderB)

if __name__ == "__main__":
    main(sys.argv[1:])

