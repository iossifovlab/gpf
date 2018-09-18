'''
Created on Nov 7, 2012

@author: Tony
'''
from __future__ import print_function
from __future__ import unicode_literals
from builtins import next
from builtins import object
import csv
import re

# default is False


def setBoolean(value):
    if value is None:
        return False

    if len(value) == 0:
        return False

    if value == "TRUE":
        return True
    elif value == "FALSE":
        return False
    else:
        print("Error: setBoolean (%s) is invalid" % (value))
        return False


def writeCSV(filename, data):
    f = open(filename, 'wb')
    writer = csv.writer(f)
    for row in data:
        writer.writerow(row)
    f.close()


def saveCSV(filename, columns, data):
    f = open(filename, 'wb')
    writer = csv.writer(f)
    writer.writerow(columns)
    for row in data:
        writer.writerow([row])
    f.close()


class CSV(object):

    def __init__(self):
        self.data = []
        self.columnNames = []
        self.columnIndex = {}

    def loadColumnNames(self):
        pass

    def getIndex(self, name):
        if name in self.columnIndex:
            return self.columnIndex[name]
        else:
            return None

    def load(self, filename):

        self.filename = filename
        try:
            inFile = open(self.filename, "rUb")
        except:
            raise

        try:
            csvReader = csv.reader(inFile, delimiter=",")
        except:
            raise

        columnNames = next(csvReader)

        validColumns = True
        if len(self.columnNames) == 0:
            self.columnNames = columnNames
        else:
            idx = 0
            for columnName in self.columnNames:
                if len(columnNames) > idx:
                    if columnNames[idx] != columnName:
                        print("Error: File column index %d (%s) is incorrect "
                              "it should be (%s)." % (
                                  idx, columnNames[idx], columnName))
                        validColumns = False
                else:
                    print("Error: File missing column index %d : %s" %
                          (idx, columnName))
                    validColumns = False
                idx += 1

        index = 0
        for columnName in self.columnNames:
            self.columnIndex[columnName] = index
            index += 1

        rowNum = 1
        if validColumns:
            for row in csvReader:
                self.data.append(row)
                rowNum += 1

        inFile.close()

        print("Loaded %d rows" % (rowNum))


def findWords(value):
    words = {}

    #    dataType = getDataType(value)
    #
    #    if dataType == 'empty':
    #        return words.keys()
    #
    #    if dataType == 'numeric':
    #        return words.keys()
    #
    #    if value == None:
    #        return words.keys()

    value = value.strip()
    value = value.lower()
    if len(value) == 0:
        return list(words.keys())

    # uncomment to filter values
    # if is_garbage(value):
    #    return words.keys()

    if value.find("\r\n") > 0:
        value = value.replace("\r\n", ' ')
    if value.find("\n") > 0:
        value = value.replace("\n", ' ')
    if value.find("\r") > 0:
        value = value.replace("\r", ' ')

    value = value.lower()

    # '-','\'',
    subs = ['\t', ',', ';', ':', '.', '!', '"', '(', ')', '[', ']', '`']

    for ch in subs:
        value = value.replace(ch, ' ')

    data = value.split(' ')
    for word in data:

        if word is None:
            break

        word = word.strip()

        if len(word) == 0:
            break

        words[word] = 0

        # if len(word)>0:
        #    if "_" in word:
        #        data2 = value.split('.')
        #        for word2 in data2:
        #            words[word2]=0
        #    else:
        #        words[word]=0

    return list(words.keys())


def is_boolean(s):

    if (s == 'true') or (s == 'false'):
        return True

    if (s == 'yes') or (s == 'no') or (s == 'not-sure'):
        return True

    return False


def is_float(s):
    match = re.match('^(?=.+)(?:[1-9]\d*|0)?(?:\.\d+)?$', s)
    if match:
        return True
    else:
        return False


def is_integer(s):
    match = re.match('^[0-9]+$', s)
    if match:
        return True
    else:
        return False


def is_number(s):

    try:
        float(s)  # for int, long and float
    except ValueError:
        try:
            complex(s)  # for complex
        except ValueError:
            return False

    return True


def is_date(s):

    match = re.match('^[0-9]+/[0-9]+/[0-9]+$', s)
    if match:
        return True

    match = re.match('^[0-9]{4}-[0-9]{2}$', s)
    if match:
        return True

    # match = re.match('[0-9]{1}:[0-9]{2}', s)
    # if match:
    #    return True

    match = re.match('^([0-9]+)(:|-)([0-9]+)$', s)
    if match:
        return True

    match = re.match('^[0-9]{2}:[0-9]{2}:[0-9]{2}$', s)
    if match:
        return True

    return False


def getDataType(s):

    if s is None:
        return 'empty'

    if len(s) == 0:
        return 'empty'

    # if is_number(s):
    #    return 'numeric'

    if is_integer(s):
        return 'numeric'

    if is_float(s):
        return 'numeric'

    # if is_boolean(s):
    #    return 'boolean'

    # if is_date(s):
    #    #return 'date'
    #    return 'string'

    return 'string'


def is_garbage(s):

    if s == "-":
        return True

    if s == "[phi suspected]":
        return True

    match = re.match('^NDAR*', s)
    if match:
        return True

    match = re.match('([0-9]+)(.)([0-9]+)(-|;)([0-9]+)(.)([0-9]+)', s)
    if match:
        return True

    match = re.search('([0-9]{5,})(.)(mo|fa|[pxs][0-9])', s)
    if match:
        return True

    return False
