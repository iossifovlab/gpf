import urllib, urllib2, json, re
from threading import Thread
from time import sleep

def compareResults(data, oldContent, indexOfTest):
	newContent = sendRequest(data)
	print "Result for variant[%d]" % (indexOfTest)
	if newContent == oldContent:
		print "YES"
	else:
		print "NO"
	print "\n"

def executeAsyncTask(numberOfIterations, variant, oldContent, indexOfTest):
	for i in range(0, numberOfIterations):
		compareResults(variant, oldContent, indexOfTest)

def sendRequest(data):
	url = 'http://localhost:8000/api/query_variants'
	print "Sending..."
	print data
	print '\n'
	req = urllib2.Request(url)
	req.add_header('Content-Type', 'application/json')
	rsp = urllib2.urlopen(req, json.dumps(data))
	content = rsp.read()
	return content	

def startAsyncTask(numberOfIterations, data, oldContent, indexOfTest):
	print "Testing variant#%d" % (indexOfTest)
	thread = Thread(target = executeAsyncTask, args = (numberOfIterations, data, oldContent, indexOfTest))
	thread.start()

variant1 = {'denovoStudies':["DalyWE2012"], 'transmittedStudies':["none"],'inChild':"prbF", 'effectTypes':"LGDs", 'variantTypes':"All", 'rarity':"ultraRare", 'genes':'All' }

variant2 = {'denovoStudies':["DalyWE2012"], 'transmittedStudies':["none"],'inChild':"prbM", 'effectTypes':"missense", 'variantTypes':"All", 'rarity':"ultraRare", 'genes':'All' }

data = []
data.append(variant1)
data.append(variant2)

results = []

for i in range(0, len(data)):
	results.append(sendRequest(data[i]))

for i in range(0, len(data)):
	startAsyncTask(1000, data[i], results[i], i)	
