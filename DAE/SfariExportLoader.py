'''
Created on Jan 31, 2013

@author: Tony
'''
from __future__ import print_function
from __future__ import division
from builtins import next
from builtins import str
from builtins import range
from past.utils import old_div
from builtins import object
import csv
import locale
import os
import sys
import tables

import SfariVariable
import SfariVariableTracker
import numpy as np
import phenoDBUtils


locale.setlocale(locale.LC_ALL, 'C')


'''
-------------------------------------------------------------------------------
class: VariablesTableParticle

    This class is used to define the structure of a PyTables Table,
    which stores the SFARI variable metatdata.

methods:

    none

-------------------------------------------------------------------------------
'''


class VariablesTableParticle(tables.IsDescription):
    variableName = tables.StringCol(itemsize=128)
    dataType = tables.StringCol(itemsize=50)
    members = tables.StringCol(itemsize=50)
    uniqueValues = tables.Int32Col()
    source = tables.StringCol(itemsize=50)


'''
------------------------------------------------------------------------------
class SfariH5File

    This class manages existing HDf5 versions of the SFARI base data. It does
    not create them, see SfariExportLoader for that.

methods:

    isOpen()
    close()
    open()
    addGroup(name)
    removeGroup(name)

-------------------------------------------------------------------------------
'''


class SfariH5File(object):

    def __init__(self, filename):
        self.filename = filename
        self.fileOpen = False
        self.handle = None
        self.memberGroups = {}
        self.members = ['fa', 'mo', 'p1', 's1', 't1']
        self.variables = {}
        self.root = None

        self.variableTracker = SfariVariableTracker.SfariVariableTracker()

    def isOpen(self):
        return self.fileOpen

    def close(self):
        if self.fileOpen:
            self.handle.flush()
            self.handle.close()
            self.fileOpen = False

    def open(self):

        if not self.fileOpen:

            if not os.path.exists(self.filename):
                print("File %s not found" % (self.filename), file=sys.stderr)
                return

            self.handle = tables.openFile(self.filename, mode="r")
            self.fileOpen = True

            self.root = self.handle.root

            # self.familiesNode = self.handle.getNode('/1','families')
            self.familiesNode = self.handle.getNode('/', 'family')
            self.families = self.familiesNode.read()
            # print ("%d families"%(len(self.families)))

            self.variablesNode = self.handle.getNode('/metadata', 'variables')

            for row in self.variablesNode.iterrows():
                variable = SfariVariable.SfariVariable(row['variableName'])
                variable.dataType = row['dataType']
                variable.uniqueValues = row['uniqueValues']
                variable.members = row['members'].split(",")
                variable.source = row['source']
                self.variables[variable.name] = variable
                self.variableTracker.add(
                    row['variableName'], row['members'], row['source'])

    def addGroup(self, name):
        if self.fileOpen:
            _group = self.handle.createGroup("/", name, name)
            self.handle.flush()

    def removeGroup(self, name):
        if self.fileOpen:
            fnode = self.handle.getNode('/', name=name, classname=None)
            fnode._f_remove(recursive=False, force=False)
            self.handle.flush()

'''
-------------------------------------------------------------------------------
class SfariExportLoader

    This class creates the HDf5 version of the SFARI base data. This class
    does alot but it is really meant to be run once.  Its purpose is to load
    the CSV SFARI files, input the variable metadata information, create a
    H5 file.  But it also returns the data structures dt and md that
    Ivan Iossifov described.  This is class can be used to return the non-H5
    version for dt and md.

    --- Updates ---

    The dt class has changed, it is much simpler now.

        its just

            dt[familyId][variableName]


            dt['11000']['ssrspa.srs_parent_raw.q16_eye_contact']

            The leading 's' is left on the variable name.


methods:

    def loadFile(self, filename, rowsToLoad=-1, startOfVariables=17,
                 includeEmptyValues=False):
    def addIndividual(self, personId, index):
    def addFamily(self, familyId, index):
    def addVariable(self, variableId, memberCode):
    def addData(self,data):
    def info(self):
    def save(self, filename):
    def load(self, filename):
    def impute(self):
    def createMetaDataReport(self, md, filename):
    def findVariable(self, key):
    def getMetadata(self, key):
    def getValueMappedArray(self, variableName, member, valueMap):
    def getValueArray(self,variableName,member):
    def saveh5(self,h5filename, title):
    def saveh5Tree(self,h5filename, title):
    def openh5(self, filename):
    def closeh5(self, filename):
    def closeh5All(self):


-------------------------------------------------------------------------------
'''


class SfariExportLoader(object):

    def __init__(self):
        self.variableTracker = SfariVariableTracker.SfariVariableTracker()
        self.families = []
        self.individuals = {}
        # self.variables = {}
        self.columns = []
        self.data = {}  # dt
        self.columnsMember = {}
        self.dataColumns = ["family", "person", "member", "variable", "value"]
        self.md = None
        self.members = ['fa', 'mo', 'p1', 's1', 't1']

        for member in self.members:
            self.individuals[member] = []

        self.h5files = {}

    # This function can be called more than once to load multiple SFARIBase
    # export files.
    # load a SFARIbase export files, one file at a time.

    def loadFile(self, filename, rowsToLoad=-1,
                 startOfVariables=17, includeEmptyValues=False):

        columns = []
        columnsMember = {}

        basename = os.path.basename(filename)[:-4]

        # print filename, basename
        inputfile = open(filename, "rUb")
        csvReader = csv.reader(inputfile, delimiter=',')

        idx = 0
        for row in csvReader:

            # if (idx%100)==0:
            #    print idx

            if rowsToLoad > -1:
                if rowsToLoad == idx:
                    break

            if idx == 0:
                i = 0
                for column in row:
                    columns.append(column)
                    self.columns.append(column)

                    columnsMember[column] = {}

                    if i < startOfVariables:
                        columnsMember[column]['member'] = 'p1'
                        columnsMember[column]['variable'] = column
                        columnsMember[column]['source'] = basename
                    else:
                        # columnsMember[column]['variable'] = column[1:]
                        columnsMember[column]['variable'] = column
                        columnsMember[column]['member'] = \
                            self.variableTracker.translate(column[0:1])
                        columnsMember[column]['source'] = basename

                    self.variableTracker.add(columnsMember[column]['variable'],
                                             columnsMember[column]['member'],
                                             columnsMember[column]['source'])

                    i += 1

            else:
                familyId = row[0]

                if familyId not in self.families:
                    self.families.append(familyId)

                for i in range(0, len(columns)):
                    variableValue = row[i].strip()
                    _varLength = len(variableValue)

                    columnName = columns[i]
                    _memberCode = columnsMember[columnName]['member']
                    variableName = columnsMember[columnName]['variable']

                    # self.addVariable(variableName, memberCode)

                    if familyId not in self.data:
                        self.data[familyId] = {}

                    self.data[familyId][variableName] = variableValue

            idx += 1

        inputfile.close()

    # track the indexes of the data for the personId
    # this is an index on personId
    def addIndividual(self, personId, index):
        if personId not in self.individuals:
            self.individuals[personId] = []
        self.individuals[personId].append(index)

    # track the indexes of the data for the familyId
    # this is an index on familyId
    def addFamily(self, familyId, index):
        if familyId not in self.families:
            self.families[familyId] = []
        self.families[familyId].append(index)


#    def addVariable(self, variableId, memberCode):
#
#        if variableId not in self.variables:
#            self.variables[variableId] = {'variable':variableId,
#                                          'members': [],
#                                          'datatype':'unknown'
#                                          }
#
#        if memberCode not in self.variables[variableId]['members']:
#            self.variables[variableId]['members'].append(memberCode)
#
#        #if variableId not in self.membersData[memberCode]:
#        #    self.membersData[memberCode][variableId]=[]
#

    # this has no index
    def addData(self, data):
        self.data.append(data)

    # print out some summary details about the loaded data
    def info(self):
        print("%s Families" % (len(self.families)))
        print("%s Individuals" % (len(self.individuals)))
        # print("%s Variables"%(len(self.variables)))
        print("%d Columns" % (len(self.columns)))
        print("%d Rows" % (len(self.data)))

    def save(self, filename):

        f = open(filename, 'wb')
        writer = csv.writer(f)

        writer.writerow(self.dataColumns)

        for data in self.data:
            writer.writerow(data)

        f.close()

    def load(self, filename):

        f = open(filename, 'rb')
        reader = csv.reader(f)

        next(reader)

        index = 0
        for data in reader:
            # if (index%100000)==0:
            #    print locale.format("%d", index, grouping=True)
            #    print data

            familyId = data[0]
            personId = data[1]
            _memberCode = data[2]
            variableName = data[3]
            _variableValue = data[4]

            self.addData(data)
            self.addIndividual(personId, index)
            self.addFamily(familyId, index)
            self.addVariable(variableName, index)

            index += 1

        f.close()

    def impute(self, everythingString=False):

        variables = {}
        md = {}
        oldway = False
        datatypes = {}

        datatypeProportionThreshold = 0.95
        for key in list(self.variableTracker.variables.keys()):
            variable = self.variableTracker.variables[key]
            variableName = variable.name

            for familyId in self.data:
                personVariables = self.data[familyId]

                variableValue = personVariables[variableName]
                varLength = len(variableValue)

                if everythingString:
                    dataType = 'string'
                else:
                    if not oldway:
                        if everythingString:
                            dataType = 'string'
                        else:
                            if variableValue in datatypes:
                                dataType = datatypes[variableValue]
                            else:
                                dataType = phenoDBUtils.getDataType(
                                    variableValue)
                                datatypes[variableValue] = dataType
                    else:
                        dataType = phenoDBUtils.getDataType(variableValue)

                if variableName not in variables:
                    variables[variableName] = {
                        'datatype': {
                            'empty': 0,
                            'numeric': 0,
                            'float': 0,
                            'integer': 0,
                            'boolean': 0,
                            'date': 0,
                            'string': 0
                        },
                        'values': {},
                        'length': 0}
                    variables[variableName]['datatype'][dataType] = 1
                    md[variableName] = {
                        'datatype': 'unknown',
                        'values': {},
                        'uniqueValues': 0,
                        'members': {}
                    }
                else:
                    variables[variableName]['datatype'][dataType] += 1

                if variableValue not in variables[variableName]['values']:
                    variables[variableName]['values'][variableValue] = 1
                else:
                    variables[variableName]['values'][variableValue] += 1

                if varLength > variables[variableName]['length']:
                    variables[variableName]['length'] = varLength

            if variableName not in variables:
                # if the variable was not added, add it now.
                # it is empty
                variables[variableName] = {
                    'datatype': {
                        'empty': 1,
                        'numeric': 0,
                        'float': 0,
                        'integer': 0,
                        'boolean': 0,
                        'date': 0,
                        'string': 0
                    },
                    'values': {},
                    'length': 0}
                md[variableName] = {
                    'datatype': 'unknown',
                    'values': {},
                    'uniqueValues': 0,
                    'members': {}
                }

        # print "There are %d variable keys"%(len(variables))

        for variableName in list(variables.keys()):

            dataTypes = variables[variableName]['datatype']
            valueDict = variables[variableName]['values']
            varLength = variables[variableName]['length']
            numValues = len(valueDict)
            dataType = 'unknown'

            if dataTypes['empty'] == numValues:
                dataType = 'unknown'

            if dataTypes['numeric'] > 0 and dataTypes['string'] > 0:
                if old_div(float(dataTypes['numeric']), float(dataTypes['string'])) > \
                        datatypeProportionThreshold:
                    dataType = 'numeric'
                elif old_div(float(dataTypes['string']), \
                    float(dataTypes['numeric'])) > \
                        datatypeProportionThreshold:
                    dataType = 'string'
                else:
                    dataType = 'string'
            elif dataTypes['numeric'] > 0:
                dataType = 'numeric'
            elif dataTypes['string'] > 0:
                dataType = 'string'

            if (dataType == 'string'):
                if numValues > 20:
                    dataType = 'text'
                else:
                    dataType = 'label'

            if dataType == 'unknown':
                dataType = 'text'

            md[variableName]['variableName'] = variableName
            md[variableName]['datatype'] = dataType
            md[variableName]['uniqueValues'] = numValues
            md[variableName]['length'] = varLength
            md[variableName]['values'] = variables[variableName]['values']

            variable = self.variableTracker.getVariable(variableName)
            variable.dataType = dataType
            variable.uniqueValues = numValues
            variable.maxLength = varLength
            variable.values = variables[variableName]['values']

        self.md = md

        return md

    def createMetaDataReport(self, md, filename):
        maxVars = 20

        try:
            f = open(filename, 'wb')
            writer = csv.writer(f)

            # Variable
            # Data Type
            # Number of Distinct values
            # Total tokens
            # Tokens with the top values
            # Mother
            # Father
            # Proband
            # Sibling
            # Most Used 0
            # Most Used 1
            # Most Used 2
            # Most Used 3
            # Most Used 4
            # Most Used 5
            # ...

            row = []
            row.append("Variable")
            row.append("Data Type")
            row.append("Number of Distinct values")
            row.append("Total tokens")
            row.append("Tokens with the top values")

            for x in sorted(self.members):
                row.append(x)

            for x in range(maxVars):
                row.append("Most Used " + str(x))

            writer.writerow(row)

            keys = sorted(md.keys())

            index = 1
            for variableName in keys:
                variable = md[variableName]
                datatype = variable['datatype']
                values = '|'.join(variable['values'])
                _uniqueValues = variable['uniqueValues']
                valueDict = md[variableName]['values']
                numUnique = len(valueDict)
                # rs = rolesS[variableName]
                sortedValues = sorted(
                    valueDict, key=valueDict.get, reverse=True)
                values = list(valueDict.values())
                tokenCount = sum(np.array(values))
                tokenInMostUsed = sum(
                    np.array([valueDict[x] for x in sortedValues[0:maxVars]]))
                _mostUsed = "\t".join(
                    [x + ";" + str(valueDict[x]) for x
                     in sortedValues[0:maxVars]])

                row = []
                # row.append(index)
                row.append(variableName)
                row.append(datatype)
                # row.append(values)
                row.append(str(numUnique))
                row.append(str(tokenCount))
                row.append(str(tokenInMostUsed))

                for member in self.members:
                    if member in md[variableName]['members']:
                        row.append(md[variableName]['members'][member])
                    else:
                        row.append("0")

                for x in sortedValues[0:maxVars]:
                    row.append(x + ";" + str(valueDict[x]))

                writer.writerow(row)
                index += 1
            f.close()
        except:
            pass

    # find a variable
    def findVariable(self, key):

        if key in self.variables:
            # print("found %s"%(key))
            return True
        else:
            # print("missing %s"%(key))
            return False

    def getMetadata(self, key):

        if key in self.md:
            varMD = self.md[key]
            return varMD
        else:
            return None

    def getValueMappedArray(self, variableName, member, valueMap):
        variableIndex = self.variables[variableName]
        vls = []
        for x in variableIndex:
            if self.data[x][2] == member:
                try:
                    value = float(valueMap[self.data[x][4]])
                    vls.append(value)
                except:
                    pass

        return vls

    def getValueArray(self, variableName, member):

        variableIndex = self.variables[variableName]

        # print self.data[variableIndex]
        #
        # for index in variableIndex:
        #    data = self.data[index]
        #
        # familyId = data[0]
        # personId = data[1]
        # memberCode = data[2]
        # variableName = data[3]
        # variableValue = data[4]

        # vls = [ float(dt[x]['variables'][variablename])
        # for x in dt.keys() if variablename in dt[x]['variables'] and
        # dt[x]['member'] == "p1" ]
        # vls = [ float(self.data[x][4])  for x in variableIndex
        # if self.data[x][2] == "p1" ]
        vls = []
        for x in variableIndex:
            if self.data[x][2] == member:
                try:
                    value = float(self.data[x][4])
                    vls.append(value)
                except:
                    pass

        return vls

    def saveh5(self, h5filename, title):
        myfilter = tables.Filters(complevel=5, complib='zlib')

        h5File = tables.openFile(h5filename, mode="w", title=title)

        families = self.families
        numberOfRows = len(families)
        nodeName = 'families'
        h5dataType = tables.StringAtom(itemsize=8)
        earray = h5File.createEArray(
            "/", nodeName, h5dataType, (0,),
            expectedrows=numberOfRows, filters=myfilter)
        earray.append(families)

        metaDataGroup = h5File.createGroup("/", 'metadata', 'metadata')
        _numberOfVariables = self.variableTracker.count()
        variablesTable = h5File.createTable(
            metaDataGroup, 'variables', VariablesTableParticle, "variables")

        for key in sorted(self.variableTracker.variableNames()):
            variable = self.variableTracker.getVariable(key)

            row = variablesTable.row
            row['variableName'] = variable.name
            row['dataType'] = variable.dataType
            row['members'] = ','.join(variable.members)
            row['uniqueValues'] = variable.uniqueValues
            row['source'] = variable.source

            row.append()

        _membergroups = {}

        numberOfRows = len(self.data)

        for key in sorted(self.variableTracker.variableNames()):
            variable = self.variableTracker.getVariable(key)

            variableName = variable.name
            dataType = variable.dataType

            # name = name.replace(".", "_")
            if dataType == "text" or dataType == "string" or \
                    dataType == "label":
                # could find out the maximum string length and use that
                length = variable.maxLength
                if length < 3:
                    length = 3
                h5dataType = tables.StringAtom(itemsize=length, dflt='NULL')
                h5dataType.flavor = 'python'
                # fillvalue="None"
            elif dataType == 'integer':
                h5dataType = tables.Int32Atom()  # @UndefinedVariable
                h5dataType.flavor = 'python'
                # fillvalue=-999999
            elif dataType == 'long':
                h5dataType = tables.Int64Atom()  # @UndefinedVariable
                h5dataType.flavor = 'python'
                # fillvalue=-999999
            elif dataType == 'float' or dataType == 'numeric':
                h5dataType = tables.Float32Atom()  # @UndefinedVariable
                h5dataType.flavor = 'python'
                # fillvalue=-999999.0
            elif dataType == 'date':
                h5dataType = tables.StringAtom(itemsize=20, dflt='NULL')
                h5dataType.flavor = 'python'
                # fillvalue="None"
            else:
                msg = "Hdf5TableGroup handler write does not support the "\
                    "type of %s %s." % (variableName, dataType)
                raise TypeError(msg)

            earray = h5File.createEArray(
                "/", variableName, h5dataType, (0,),
                expectedrows=numberOfRows, filters=myfilter)

            data = []
            for familyId in self.families:
                variableValue = self.data[familyId][variableName]

                if dataType == 'integer':
                    try:
                        variableValue = int(variableValue)
                    except ValueError:
                        # print "ValueError error int ", variableName, ", ",
                        # variableValue, ",", sys.exc_info()[0]
                        variableValue = None
                elif dataType == 'long':
                    try:
                        variableValue = int(variableValue)
                    except ValueError:
                        # print "ValueError error float ", variableName, ", ",
                        # variableValue, ",", sys.exc_info()[0]
                        variableValue = None
                elif dataType == 'float' or dataType == 'numeric':
                    try:
                        variableValue = float(variableValue)
                    except ValueError:
                        # print "ValueError error float ", variableName, ", ",
                        # variableValue, ",", sys.exc_info()[0]
                        variableValue = None
                elif dataType == 'date':
                    pass

                data.append(variableValue)

            try:
                earray.append(data)
            except ValueError:
                print("ValueError error with ", variableName, ", ", \
                    sys.exc_info()[0])

        h5File.flush()
        h5File.close()

    def saveh5Tree(self, h5filename, title):
        h5File = tables.openFile(h5filename, mode="w", title=title)

        families = self.families
        numberOfRows = len(families)
        nodeName = 'families'
        h5dataType = tables.StringAtom(itemsize=8)
        earray = h5File.createEArray(
            "/", nodeName, h5dataType, (0,), expectedrows=numberOfRows)
        earray.append(families)

        metaDataGroup = h5File.createGroup("/", 'metadata', 'metadata')
        _numberOfVariables = len(self.variables)

        variablesTable = h5File.createTable(
            metaDataGroup, 'variables', VariablesTableParticle, "variables")

        for key in sorted(self.variables.keys()):
            variable = self.variables[key]
            variableName = variable['variable']
            dataType = variable['datatype']
            members = ','.join(variable['members'])
            uniqueValues = variable['uniqueValues']

            row = variablesTable.row
            row['variableName'] = variableName
            row['dataType'] = dataType
            row['members'] = members
            row['uniqueValues'] = uniqueValues

            row.append()

        membergroups = {}
        for member in self.members:
            membergroups[member] = h5File.createGroup("/", member, member)

            individuals = self.individuals[member]
            numberOfRows = len(individuals)
            # print  member , numberOfRows
            nodeName = 'personId'
            h5dataType = tables.StringAtom(itemsize=8)
            earray = h5File.createEArray(
                membergroups[member], nodeName, h5dataType, (0,),
                expectedrows=numberOfRows)
            earray.append(individuals)

        for key in self.variables:
            variable = self.variables[key]
            variableName = variable['variable']
            dataType = variable['datatype']
            # name = name.replace(".", "_")
            members = variable['members']
            # print name,dataType,members
            for member in members:

                individuals = self.individuals[member]
                numberOfRows = len(individuals)
                # print  member , numberOfRows

                if dataType == "text" or dataType == "string" or \
                        dataType == "label":
                    # could find out the maximum string length and use that
                    length = variable["length"]
                    if length < 3:
                        length = 3
                    h5dataType = tables.StringAtom(
                        itemsize=length, dflt='NULL')
                    h5dataType.flavor = 'python'
                    # fillvalue="None"
                elif dataType == 'integer':
                    h5dataType = tables.Int32Atom()  # @UndefinedVariable
                    h5dataType.flavor = 'python'
                    # fillvalue=-999999
                elif dataType == 'long':
                    h5dataType = tables.Int64Atom()  # @UndefinedVariable
                    h5dataType.flavor = 'python'
                    # fillvalue=-999999
                elif dataType == 'float' or dataType == 'numeric':
                    h5dataType = tables.Float32Atom()  # @UndefinedVariable
                    h5dataType.flavor = 'python'
                    # fillvalue=-999999.0
                elif dataType == 'date':
                    h5dataType = tables.StringAtom(itemsize=20, dflt='NULL')
                    h5dataType.flavor = 'python'
                    # fillvalue="None"
                else:
                    msg = "Hdf5TableGroup handler write does not support "\
                        "the type of %s." % dataType
                    raise TypeError(msg)

                earray = h5File.createEArray(
                    membergroups[member], variableName, h5dataType, (0,),
                    expectedrows=numberOfRows)

                data = []
                for individual in individuals:

                    # if variableName == 'Sibling_Sex':
                    #    print 'here'

                    if variableName in self.data[individual]['variables']:
                        variableValue = self.data[individual][
                            'variables'][variableName]

                        if dataType == 'integer':
                            try:
                                variableValue = int(variableValue)
                            except ValueError:
                                print("ValueError error int ", \
                                    variableName, ", ", variableValue, ",", \
                                    sys.exc_info()[0], file=sys.stderr)
                                variableValue = None
                        elif dataType == 'long':
                            try:
                                variableValue = int(variableValue)
                            except ValueError:
                                print("ValueError error float ", \
                                    variableName, ", ", variableValue, ",", \
                                    sys.exc_info()[0], file=sys.stderr)
                                variableValue = None
                        elif dataType == 'float' or dataType == 'numeric':
                            try:
                                variableValue = float(variableValue)
                            except ValueError:
                                print("ValueError error float ", \
                                    variableName, ", ", variableValue, ",", \
                                    sys.exc_info()[0], file=sys.stderr)
                                variableValue = None
                        elif dataType == 'date':
                            pass

                    else:

                        if dataType == 'integer':
                            variableValue = None
                        elif dataType == 'long':
                            variableValue = None
                        elif dataType == 'float' or dataType == 'numeric':
                            variableValue = None
                        elif dataType == 'date':
                            variableValue = ""
                        else:
                            variableValue = ""

                    # earray.append([variableValue])
                    data.append(variableValue)  # this is much faster

                # self.membersData[member][variable['variable']].append(value)
                # earray.append(self.membersData[member][variable['variable']])
                try:
                    earray.append(data)
                except ValueError:
                    print("ValueError error with ", variableName, ", ", \
                        sys.exc_info()[0], file=sys.stderr)

        h5File.flush()
        h5File.close()

    def openh5(self, filename):

        if filename in self.h5files:
            h5file = self.h5files[filename]

        else:
            h5file = SfariH5File(filename)
            h5file.open()

            self.variableTracker = h5file.variableTracker

            self.h5files[filename] = h5file

        return h5file

    def closeh5(self, filename):
        if filename in self.h5files:
            h5file = self.h5files[filename]
            h5file.close()

    def closeh5All(self):
        for filename in self.h5files:
            h5file = self.h5files[filename]
            h5file.close()
