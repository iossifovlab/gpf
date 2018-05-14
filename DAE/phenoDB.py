from __future__ import print_function
import tables
import types
import csv

import SfariExportLoader
from phenoDBUtils import getDataType, findWords
import scipy.stats as stats


'''
------------------------------------------------------------------------------
 2/14/2013 -
            This function now loads a each variable independently and does
            not strip the family member leading character.

 Inputs:
     files - an array of fully qualified filenames
             These files are downloaded from the SFARI Base website.

    rowsToLoad - (optional) Limits the number of rows to load from the files.
                Used for debugging.


 Outputs:
    dt - a Python dictionary with the following structure

        dt[personId]
        dt[personId]['family']
        dt[personId]['member']
        dt[personId]['variables']
        dt[personId]['variables'][variableName]=variableValue

    vars - a SfariVariableTracker class


    dt,vars = loadFromRawTable("sfari14.csv")

    dt,vars = loadFromRawTable(["sfari14.csv","sfari15.csv"])

------------------------------------------------------------------------------
'''
'''
PhenoTalbe design (NO LINE AND COLUMN NUMBERS)
Values are either not present (spares matrix) represented as an empty string
in the excell or string

dt.variables;
returns a set of variable names

dt.families
returns the set of family ids

dt.get_variable(variable)
returns an *dictionary* of "famid: value" for all the non-empty values

dt.get_family(family);
returns a *dictionary* for "varname: value" for all the non-empty values

dt.get_value(family,variable);
returns the value of variable in family of present or throws an Exception

dt.is_present(family,variable);
returns True if the value of variable is non-null for family
'''
''' interface with prescribed order of families and variables
Values are either not present (sparse matrix) represented as an empty string
in the excel or string

PhenoTalbe design (NO LINE AND COLUMN NUMBERS)

dt.variables
a list of variable names

dt.familes
a list of family ids

dt.get_variable(variable)
returns an np.array with len(families) elements with strings elements

dt.get_family(family);
returns an np.array with len(variables) elements with strings elements

dt.get_value(family,variable);
returns the value of variable in family if the value present otherwise throws
and excpetion

dt.is_present(family,variable);
returns True if the value of variable is non-null for family
'''
'''
# rawTableFactor():
dt = rawTableFactory(".../.csv")
dt = rawTableFactory(".../.h5")


impute(dt)

test 1
dt = rawTableFactory(".../.csv")
impute(dt)

test 2
dt = rawTableFactory(".../.h5")
impute(dt)


    # CSV
    for family_id in dt.familes:
        for variable_id in dt.variables:
            value = dt.get_value(family_id,variable_id);
            datatype = imput_value_datatype(value)

    # H5
    for variable_id in dt.variables:
        values = dt.get_values(variable_id)

'''


class TableInterface:

    def __init__(self):
        # print 'TableInterface::__init__()'

        self.sfariLoader = SfariExportLoader.SfariExportLoader()

        self.variables = []
        self.families = []

        # self.data = None
        # self.variableTracker = None

    def load(self):
        # print 'TableInterface::load()'
        pass

    # returns an np.array with len(families) elements with strings elements
    def get_variable(self, variable):
        pass

    # returns an np.array with len(variables) elements with strings elements
    def get_family(self, family):
        pass

    # returns the value of variable in family if the value present otherwise
    # throws and excpetion
    def get_value(self, family, variable):
        pass

    # returns True if the value of variable is non-null for family
    def is_present(self, family, variable):
        pass


class TableInterfaceCSV(TableInterface):

    def __init__(self):
        TableInterface.__init__(self)

    def load(self, filename):
        self.sfariLoader.loadFile(filename)
        self.data = self.sfariLoader.data
        self.variables = self.sfariLoader.variableTracker.variableNames()
        # self.families = self.sfariLoader.data.keys()
        self.families = self.sfariLoader.families

    def get_variable(self, variableName):
        values = []
        for familyId in self.families:
            if variableName in self.data[familyId]:
                variableValue = self.data[familyId][variableName]
                values.append(variableValue)
        return values

    def get_family(self, familyId):
        if familyId in self.data:
            return self.data[familyId]
        else:
            raise 'familyId does not exist'

    def get_value(self, familyId, variableId):
        if familyId in self.data:
            if variableId in self.data[familyId]:
                return self.data[familyId][variableId]
            else:
                raise 'variableId does not exist'
        else:
            raise 'familyId does not exist'

    def is_present(self, familyId, variableId):
        if familyId in self.data:
            if variableId in self.data[familyId]:
                return True
            else:
                return False
        else:
            return False


class TableInterfaceH5(TableInterface):

    def __init__(self):
        TableInterface.__init__(self)
        self.variableDataCache = {}

    def load(self, filename):
        self.h5file = self.sfariLoader.openh5(filename)

        try:
            # self.familiyData = self.h5file.root._f_getChild('family')[:]
            self.familiyData = self.h5file.root._f_getChild('families')[:]
        except tables.NoSuchNodeError:
            raise

        self.families = self.familiyData.tolist()
        self.variables = sorted(self.h5file.variables.keys())

        self.md = {}
        for variableName in self.h5file.variables.keys():
            variable = self.h5file.variables[variableName]
            self.md[variableName] = {
                'name': variable.name,
                'datatype': variable.dataType,
                'values': variable.values,
                'uniqueValues': variable.uniqueValues,
                'members': variable.members,
                'source': variable.source}

    # returns an np.array with len(families) elements with strings elements
    def get_variable(self, variableId):
        try:
            if variableId not in self.variableDataCache:
                variableData = self.h5file.root._f_getChild(variableId)[:]
                self.variableDataCache[variableId] = variableData
            else:
                return self.variableDataCache[variableId]
        except tables.NoSuchNodeError:
            # msg = "variableId %s does not exist"%(variableId)
            # print msg
            variableData = None

        return variableData

    def get_family(self, familyId):
        familyData = {}
        if familyId in self.families:
            index = self.families.index(familyId)
            for variableId in self.variables:
                variableData = self.get_variable(variableId)
                familyData[variableId] = variableData[index]
            return familyData
        else:
            raise 'familyId does not exist'

    def get_value(self, familyId, variableId):
        if familyId in self.families:
            if variableId in self.variables:
                variableData = self.get_variable(variableId)
            else:
                raise 'variableId does not exist'
        else:
            raise 'familyId does not exist'

        index = self.families.index(familyId)

        return variableData[index]

    def is_present(self, familyId, variableId):
        pass

    def getVariableMetaData(self, variableName):
        if variableName in self.md:
            return self.md[variableName]
        else:
            return {}


def imputeNew(dt):

    variables = {}
    md = {}
    datatypes = {}

    datatypeProportionThreshold = 0.95
    for variableName in dt.variables:

        # variable = dt.variableTracker.variables[key]
        # variableName = variable.name

        values = dt.get_variable(variableName)

        # for familyId in dt.data:
        #    personVariables = dt.data[familyId]
        #    variableValue = personVariables[variableName]

        for variableValue in values:

            varLength = len(variableValue)

            if variableValue in datatypes:
                dataType = datatypes[variableValue]
            else:
                dataType = getDataType(variableValue)
                datatypes[variableValue] = dataType

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
                'length': 0
            }
            md[variableName] = {
                'datatype': 'unknown',
                'values': {},
                'uniqueValues': 0,
                'members': {}
            }

    # print "There are %d variable keys"%(len(variables))

    for variableName in variables.keys():

        dataTypes = variables[variableName]['datatype']
        valueDict = variables[variableName]['values']
        varLength = variables[variableName]['length']

        numValues = len(valueDict)

        dataType = 'unknown'

        if dataTypes['empty'] == numValues:
            dataType = 'unknown'

        if dataTypes['numeric'] > 0 and dataTypes['string'] > 0:
            if float(dataTypes['numeric']) / float(dataTypes['string']) > \
                    datatypeProportionThreshold:

                dataType = 'numeric'
            elif float(dataTypes['string']) / float(dataTypes['numeric']) > \
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

        # variable = dt.variableTracker.getVariable(variableName)
        # variable.dataType = dataType
        # variable.uniqueValues = numValues
        # variable.maxLength = varLength
        # variable.values = variables[variableName]['values']

    return md


def rawTableFactory(filename):

    # daeDir = os.environ['DAE_DB_DIR']
    # _config = ConfigParser({'wd':daeDir})
    # _config.optionxform = lambda x: x
    # confFile = os.path.join(daeDir,"pheno.conf")
    # _config.read(confFile)
    # phenoDir = _config.get('PhenoInfo', 'phenoDir')
    # filename = os.path.join(phenoDir,filename)

    if filename[len(filename) - 4:].lower() == ".csv":

        tableInterface = TableInterfaceCSV()
        tableInterface.load(filename)

    elif filename[len(filename) - 3:].lower() == ".h5":

        tableInterface = TableInterfaceH5()
        tableInterface.load(filename)

    return tableInterface


def loadFromRawTable(files, rowsToLoad=-1):

    sfariLoader = SfariExportLoader.SfariExportLoader()

    loadFiles = []
    if type(files) == list:  # @IgnorePep8
        loadFiles = files
    else:
        loadFiles.append(files)

    for filename in loadFiles:
        # sfariLoader.loadFile(filename, rowsToLoad=500)
        sfariLoader.loadFile(filename)

    return sfariLoader.data, sfariLoader.variableTracker

# given dt
# returns md
# meta data :
#
#    md[variableName]['datatype'] = str  label, text, numeric, unknown
#    md[variableName]['values'][value] = count
#    md[variableName]['member'][member] = count;

# bug?
# md[variableName]['values'] = sorted(variables[variableName]['values'].keys())


def imputeMetaData(dt, variableTracker):

    sfariLoader = SfariExportLoader.SfariExportLoader()
    sfariLoader.data = dt
    sfariLoader.variableTracker = variableTracker
    sfariLoader.impute()

    return sfariLoader.md


def createMetaDataReport(md, filename):
    sfariLoader = SfariExportLoader.SfariExportLoader()
    # print sfariLoader.members
    sfariLoader.createMetaDataReport(md, filename)


def saveMetaData(md, filename):

    f = open(filename, 'wb')
    # ,lineterminator="\n") # delimiter=',',quoting=csv.QUOTE_MINIMAL)
    writer = csv.writer(f)

    row = []
    row.append("index")
    row.append("variableName")
    row.append("datatype")
    row.append("uniqueValues")
    row.append("values")
    writer.writerow(row)

    keys = sorted(md.keys())

    index = 1
    for variableName in keys:
        variable = md[variableName]
        datatype = variable['datatype']

        valuesStr = "|".join(
            [v + ";" + str(n) for v, n
             in sorted(variable['values'].items(), key=lambda x: -x[1])])

        # valuesStr = '|'.join(sorted(variable['values'].keys()))
        uniqueValues = variable['uniqueValues']

        row = []
        row.append(index)
        row.append(variableName)
        row.append(datatype)
        row.append(uniqueValues)
        row.append(valuesStr)

        writer.writerow(row)
        index += 1
    f.close()


# load CSV
# return a md
def loadMetaData(mdFilename):
    md = {}

    inputfile = open(mdFilename, "rUb")
    csvReader = csv.reader(inputfile, delimiter=',')

    for row in csvReader:
        md[row[1]] = {}
        md[row[1]]['datatype'] = row[2]
        md[row[1]]['uniqueValues'] = row[3]
        md[row[1]]['values'] = row[4].split('|')

    inputfile.close()

    return md


# given
#     filename
# return
#    dictionary of family ids
def loadFamilyList(filename):
    familyList = []

    inputfile = open(filename, "rUb")
    csvReader = csv.reader(inputfile, delimiter=',')

    _column = next(csvReader)
    for row in csvReader:
        familyList.append(row[0])

    inputfile.close()

    return familyList


def createWordBag(dt, md):
    wordBag = {}

    for familyId in dt.keys():
        familyDictionary = dt[familyId]

        for variableName in familyDictionary:
            if variableName in md:
                datatype = md[variableName]['datatype']
                if datatype == 'text' or datatype == 'label':
                    variableValue = familyDictionary[variableName]

                    words = findWords(variableValue)

                    for word in words:
                        if word not in wordBag:
                            wordBag[word] = {'all': 0, 'family': {}}

                        if familyId not in wordBag[word]['family']:
                            wordBag[word]['family'][familyId] = True

                        wordBag[word]['all'] += 1
                else:
                    continue
    return wordBag


def createWordBag2(dt, md, testSet):
    wordBag = {}

    # total in dt
    _totalDT = len(dt)

    # total in testSet
    _totalTest = len(testSet)

    # print("%d %d"%(totalDT,totalTest))

    for familyId in dt.keys():

        familyDictionary = dt[familyId]

        for variableName in familyDictionary:
            if variableName in md:

                datatype = md[variableName]['datatype']
                if datatype == 'text' or datatype == 'label':

                    variableValue = familyDictionary[variableName]

                    words = findWords(variableValue)

                    if variableName not in wordBag:
                        wordBag[variableName] = {}

                    wordBagDict = wordBag[variableName]

                    for word in words:
                        if word not in wordBagDict:
                            wordBagDict[word] = {'all': 1, 'test': 0}
                        else:
                            wordBagDict[word]['all'] += 1

                        if familyId in testSet:
                            wordBagDict[word]['test'] += 1
                else:
                    continue

    return wordBag


def createWordBagH5(dt, md, testSet):
    wordBag = {}

    # total in dt
    # totalDT = len(dt)
    # total in testSet
    # totalTest = len(testSet)
    # print("%d %d"%(totalDT,totalTest))
    # self.variables = []
    # self.families = []

    for familyId in dt.families:
        print(familyId)
        # familyDictionary = dt[familyId]

        for variableName in dt.variables:

            print("\t", variableName)

#            if variableName in md:
#
#                datatype = md[variableName]['datatype']
#                if datatype == 'text' or datatype == 'label':
#
#                    variableValue = familyDictionary[variableName]
#
#                    words = findWords(variableValue)
#
#                    if variableName not in wordBag:
#                        wordBag[variableName] = {}
#
#                    wordBagDict = wordBag[variableName]
#
#                    for word in words:
#                        if word not in wordBagDict:
#                            wordBagDict[word]={'all':1, 'test':0}
#                        else:
#                            wordBagDict[word]['all']+=1
#
#                        if familyId in testSet:
#                            wordBagDict[word]['test']+=1
#                else:
#                    continue

    return wordBag


def saveWordBag2(wordBag, wordBagFilename):
    f = open(wordBagFilename, 'wb')
    writer = csv.writer(f)

    row = []
    row.append("variable")
    row.append("word")
    # row.append("type")
    row.append("count in entire family set")
    row.append("count in test family set")
    writer.writerow(row)

    keys = sorted(wordBag.keys())
    for variableName in keys:
        wordBagDict = wordBag[variableName]

        for wordKey in wordBagDict:
            counts = wordBagDict[wordKey]

            row = []
            row.append(variableName)
            row.append(wordKey)
            row.append(counts['all'])
            row.append(counts['test'])

            writer.writerow(row)

    f.close()


def saveWordBag(wordBag, wordBagFilename):
    f = open(wordBagFilename, 'wb')
    writer = csv.writer(f)

    row = []
    row.append("word")
    row.append("count for all families")
    # row.append("family")
    writer.writerow(row)

    keys = sorted(wordBag.keys())
    for key in keys:
        word = wordBag[key]
        row = []
        row.append(key)
        row.append(word['all'])
        # row.append(len(word['family']))
        writer.writerow(row)
    f.close()


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

def runHyperGeometricTest(dt, md, wordBag, setA, setB, outfilename):

    totalCountInSetA = len(setA)
    totalCountInSetB = len(setB)

    f = open(outfilename, 'wb')
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
        hg = stats.hypergeom(totalCountInSetA, countInA, countInB)
        x = 0.0
        xb = x
        hgMean = hg.mean()
        xs = hgMean - (x - hgMean)
        if x < hg.mean():
            xs = x
            xb = hgMean + (hgMean - x)
            moreOrLess = "less"
        else:
            moreOrLess = "More"

        # print xs,xb
        # print hg.cdf(xs), hg.cdf(xb), 1.0 - float(hg.cdf(xb))
        # if hg.cdf(xb)>1.0:
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


# returns the families in a dt
def getFamilyList(dt):
    return dt.keys()
